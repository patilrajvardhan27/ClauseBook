# Reciprocal rank fusion of a lexical (BM25) and a vector (kNN) search over the same index.
from __future__ import annotations

from clausebook_core.config.settings import Settings

RRF_K = 60  # standard RRF damping constant; higher values favor documents ranked well by both retrievers


# Runs BM25 and/or kNN against OpenSearch; mode picks which retrievers feed the ranking.
# "bm25" and "knn" exist so ml/eval/acord_eval.py can compare each retriever against the
# fused "hybrid" mode this function defaults to for every other caller.
def hybrid_search(
    settings: Settings, query: str, clause_type: str | None, top_k: int = 20, mode: str = "hybrid"
) -> list[dict]:
    try:
        from opensearchpy import OpenSearch
    except ImportError:
        return []

    client = OpenSearch(hosts=[settings.opensearch_url])
    if not client.indices.exists(index=settings.opensearch_index_precedent):
        return []

    if mode == "bm25":
        hits = _bm25_search(client, settings, query, clause_type, top_k)
        return [{"precedent_id": doc_id, "clause_text": text, "score": 1.0 / (rank + 1)} for rank, (doc_id, text) in enumerate(hits)]
    if mode == "knn":
        hits = _knn_search(client, settings, query, clause_type, top_k)
        return [{"precedent_id": doc_id, "clause_text": text, "score": 1.0 / (rank + 1)} for rank, (doc_id, text) in enumerate(hits)]

    bm25_hits = _bm25_search(client, settings, query, clause_type, top_k * 3)
    knn_hits = _knn_search(client, settings, query, clause_type, top_k * 3)
    fused = _reciprocal_rank_fusion(bm25_hits, knn_hits)
    return fused[:top_k]


# Runs a BM25 text match, optionally filtered by clause type; returns (id, clause_text) pairs.
def _bm25_search(client, settings: Settings, query: str, clause_type: str | None, size: int) -> list[tuple[str, str]]:
    filters = [{"term": {"clause_type": clause_type}}] if clause_type else []
    body = {"size": size, "query": {"bool": {"must": [{"match": {"clause_text": query}}], "filter": filters}}}
    response = client.search(index=settings.opensearch_index_precedent, body=body)
    return [(hit["_id"], hit["_source"].get("clause_text", "")) for hit in response["hits"]["hits"]]


# Runs a kNN search on the query's embedding, optionally filtered by clause type; returns (id, clause_text) pairs.
def _knn_search(client, settings: Settings, query: str, clause_type: str | None, size: int) -> list[tuple[str, str]]:
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
    return [(hit["_id"], hit["_source"].get("clause_text", "")) for hit in response["hits"]["hits"]]


# Combines several ranked (id, clause_text) lists into one score per document, keeping each id's text.
def _reciprocal_rank_fusion(*ranked_lists: list[tuple[str, str]]) -> list[dict]:
    scores: dict[str, float] = {}
    text_by_id: dict[str, str] = {}
    for ranked in ranked_lists:
        for rank, (doc_id, text) in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
            text_by_id.setdefault(doc_id, text)
    ranked_ids = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{"precedent_id": doc_id, "clause_text": text_by_id[doc_id], "score": score} for doc_id, score in ranked_ids]
