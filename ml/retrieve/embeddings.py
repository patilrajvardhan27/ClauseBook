"""Sentence embeddings for kNN retrieval.

Loaded lazily so importing this module costs nothing when the embedding
model is not installed (CI's unit-test tier never needs it; only the
eval and worker tiers do).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from clausebook_core.config.settings import Settings


@lru_cache
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_text(settings: Settings, text: str) -> list[float]:
    model = _load_model(settings.embedding_model)
    vector: np.ndarray = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(settings: Settings, texts: list[str]) -> list[list[float]]:
    model = _load_model(settings.embedding_model)
    vectors: np.ndarray = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return vectors.tolist()
