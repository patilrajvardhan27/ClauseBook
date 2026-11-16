"""Cross-encoder reranking of the top candidates from hybrid retrieval.

A cross-encoder scores (query, candidate) pairs jointly, which is slower
than the bi-encoder used for kNN but catches ranking errors fusion leaves
behind -- it only needs to run on the top 50, not the full index.
"""
from __future__ import annotations

from functools import lru_cache

from clausebook_core.config.settings import Settings


@lru_cache
def _load_reranker(model_name: str):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def rerank(settings: Settings, query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    model = _load_reranker(settings.reranker_model)
    pairs = [(query, c["clause_text"]) for c in candidates]
    scores = model.predict(pairs)
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)
    return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
