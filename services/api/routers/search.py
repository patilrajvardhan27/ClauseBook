"""Hybrid precedent search: BM25 plus kNN, fused with reciprocal rank fusion,
filtered by clause type. See ml/retrieve/hybrid.py for the fusion itself;
this router only shapes the request and the response.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from clausebook_core.config.settings import Settings
from ml.retrieve.hybrid import hybrid_search
from services.api.deps import get_app_settings

router = APIRouter()


@router.get("")
def search(q: str, clause_type: str | None = None, settings: Settings = Depends(get_app_settings)) -> dict:
    hits = hybrid_search(settings, query=q, clause_type=clause_type)
    return {"query": q, "results": hits}
