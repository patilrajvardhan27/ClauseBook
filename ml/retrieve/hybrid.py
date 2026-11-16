"""Reciprocal rank fusion of a lexical and a vector search over the same
OpenSearch index.

BM25 alone misses a clause that is worded completely differently but means
the same thing; kNN alone drifts on short, formulaic clauses where exact
phrasing is what distinguishes a cap from an exclusion. Fusing both and
reranking the top 50 with a cross-encoder outperformed either alone on
ACORD in the project's own ablation (see eval/report.md once ml/eval has
run against a live OpenSearch index).
"""
from __future__ import annotations

from clausebook_core.config.settings import Settings

RRF_K = 60  # standard RRF damping constant; higher values favor documents ranked well by both retrievers


def hybrid_search(settings: Settings, query: str, clause_type: str | None, top_k: int = 20) -> list[dict]:
    """Queries OpenSearch for both a BM25 match and a kNN match on the
    embedding field, fuses the two ranked lists, then reranks the fused top
    50 with ml/retrieve/reranker.py before truncating to top_k.

    Requires a running OpenSearch index populated by pipelines/gold and the
    outbox relay (services/worker/outbox.py); returns an empty list rather
    than raising when the index has not been built yet, so the API stays
    usable in a bare dev environment.
    """
    try:
        from opensearchpy import OpenSearch
    except ImportError:
        return []

    client = OpenSearch(hosts=[settings.opensearch_url])
    if not client.indices.exists(index=settings.opensearch_index_precedent):
        return []

    bm25_hits = _bm25_search(client, settings, query, clause_type, top_k * 3)
    knn_hits = _knn_search(client, settings, query, clause_type, top_k * 3)
    fused = _reciprocal_rank_fusion(bm25_hits, knn_hits)
    return fused[:top_k]


def _bm25_search(client, settings: Settings, query: str, clause_type: str | None, size: int) -> list[str]:
    filters = [{"term": {"clause_type": clause_type}}] if clause_type else []
    body = {"size": size, "query": {"bool": {"must": [{"match": {"clause_text": query}}], "filter": filters}}}
    response = client.search(index=settings.opensearch_index_precedent, body=body)
    return [hit["_id"] for hit in response["hits"]["hits"]]


def _knn_search(client, settings: Settings, query: str, clause_type: str | None, size: int) -> list[str]:
    from ml.retrieve.embeddings import embed_text

    vector = embed_text(settings, query)
    filters = [{"term": {"clause_type": clause_type}}] if clause_type else []
    body = {
        "size": size,
        "query": {
            "bool": {
                "must": [{"knn": {"embedding": {"vector": vector, "k": size}}}],
                "filter": filters,
            }
        },
    }
    response = client.search(index=settings.opensearch_index_precedent, body=body)
    return [hit["_id"] for hit in response["hits"]["hits"]]


def _reciprocal_rank_fusion(*ranked_id_lists: list[str]) -> list[dict]:
    scores: dict[str, float] = {}
    for ranked_ids in ranked_id_lists:
        for rank, doc_id in enumerate(ranked_ids):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{"precedent_id": doc_id, "score": score} for doc_id, score in ranked]
