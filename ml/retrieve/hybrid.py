# Reciprocal rank fusion of a lexical (BM25) and a vector (kNN) search over the same index.
from __future__ import annotations

from clausebook_core.config.settings import Settings

RRF_K = 60  # standard RRF damping constant; higher values favor documents ranked well by both retrievers


# Runs BM25 and kNN against OpenSearch and fuses the two ranked lists; empty if the index isn't built yet.
def hybrid_search(settings: Settings, query: str, clause_type: str | None, top_k: int = 20) -> list[dict]:
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


# Runs a BM25 text match, optionally filtered by clause type.
def _bm25_search(client, settings: Settings, query: str, clause_type: str | None, size: int) -> list[str]:
    filters = [{"term": {"clause_type": clause_type}}] if clause_type else []
    body = {"size": size, "query": {"bool": {"must": [{"match": {"clause_text": query}}], "filter": filters}}}
    response = client.search(index=settings.opensearch_index_precedent, body=body)
    return [hit["_id"] for hit in response["hits"]["hits"]]


# Runs a kNN search on the query's embedding, optionally filtered by clause type.
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


# Combines several ranked id lists into one score per document.
def _reciprocal_rank_fusion(*ranked_id_lists: list[str]) -> list[dict]:
    scores: dict[str, float] = {}
    for ranked_ids in ranked_id_lists:
        for rank, doc_id in enumerate(ranked_ids):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{"precedent_id": doc_id, "score": score} for doc_id, score in ranked]
