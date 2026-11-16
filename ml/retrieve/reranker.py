# Cross-encoder reranking of the top candidates from hybrid retrieval.
from __future__ import annotations

from functools import lru_cache

from clausebook_core.config.settings import Settings


# Loads and caches the cross-encoder reranker model by name.
@lru_cache
def _load_reranker(model_name: str):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


# Scores each candidate against the query and returns them sorted by rerank score.
def rerank(settings: Settings, query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    model = _load_reranker(settings.reranker_model)
    pairs = [(query, c["clause_text"]) for c in candidates]
    scores = model.predict(pairs)
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)
    return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
