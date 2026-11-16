# Compares BM25, kNN, hybrid (RRF) and reranked hybrid against ACORD's lawyer-rated query/clause pairs.
#
# ACORD (The Atticus Project, CC BY 4.0) pairs a query with clauses rated
# for relevance. This needs a live, populated OpenSearch index: run
# pipelines/seed/cuad_precedent.py and let the worker relay the outbox
# first. Expects eval/fixtures/acord_queries.csv with columns query_id,
# query_text, precedent_id, relevance (0-3), one row per rated pair.
#
# Usage: PYTHONPATH=.:libs python3 ml/eval/acord_eval.py
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from clausebook_core.config.settings import get_settings

from ml.eval.retrieval_metrics import ndcg_at_k, recall_at_k
from ml.retrieve.hybrid import hybrid_search

ACORD_PATH = Path("eval/fixtures/acord_queries.csv")
TOP_K_NDCG = 5
TOP_K_RECALL = 20
MODES = ["bm25", "knn", "hybrid", "hybrid+rerank"]


# One query's rated clauses: precedent_id -> relevance score (0-3).
def _load_acord_queries() -> dict[str, dict[str, int]]:
    by_query: dict[str, dict[str, int]] = defaultdict(dict)
    with ACORD_PATH.open() as f:
        for row in csv.DictReader(f):
            by_query[row["query_text"]][row["precedent_id"]] = int(row["relevance"])
    return by_query


# Runs one query through one retrieval mode and scores it against ACORD's relevance judgments.
def _score_query(query_text: str, relevance_by_id: dict[str, int], mode: str) -> dict:
    settings = get_settings()
    search_mode = "hybrid" if mode == "hybrid+rerank" else mode
    hits = hybrid_search(settings, query=query_text, clause_type=None, top_k=TOP_K_RECALL, mode=search_mode)

    if mode == "hybrid+rerank" and hits:
        from ml.retrieve.reranker import rerank as rerank_hits

        hits = rerank_hits(settings, query_text, hits)

    ranked_relevances = [relevance_by_id.get(hit["precedent_id"], 0) for hit in hits]
    ranked_relevant_flags = [relevance_by_id.get(hit["precedent_id"], 0) > 0 for hit in hits]
    total_relevant = sum(1 for score in relevance_by_id.values() if score > 0)

    return {
        "ndcg_at_5": ndcg_at_k(ranked_relevances, TOP_K_NDCG),
        "recall_at_20": recall_at_k(ranked_relevant_flags, total_relevant, TOP_K_RECALL),
    }


# Runs every query through every mode and averages the metrics, as one row per mode.
def run_acord_eval() -> dict[str, dict[str, float]]:
    queries = _load_acord_queries()
    results: dict[str, dict[str, float]] = {}

    for mode in MODES:
        ndcg_scores, recall_scores = [], []
        for query_text, relevance_by_id in queries.items():
            scored = _score_query(query_text, relevance_by_id, mode)
            ndcg_scores.append(scored["ndcg_at_5"])
            recall_scores.append(scored["recall_at_20"])
        results[mode] = {
            "ndcg_at_5": sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0,
            "recall_at_20": sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
        }

    return results


def main() -> None:
    if not ACORD_PATH.exists():
        raise FileNotFoundError(f"{ACORD_PATH} not found; download ACORD and place it there first")

    results = run_acord_eval()
    print(f"{'mode':<10} {'nDCG@5':>8} {'Recall@20':>10}")
    for mode, metrics in results.items():
        print(f"{mode:<10} {metrics['ndcg_at_5']:>8.3f} {metrics['recall_at_20']:>10.3f}")


if __name__ == "__main__":
    main()
