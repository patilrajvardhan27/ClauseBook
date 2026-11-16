# Hybrid precedent search; the fusion itself lives in ml/retrieve/hybrid.py.
from __future__ import annotations

from clausebook_core.config.settings import Settings
from fastapi import APIRouter, Depends

from ml.retrieve.hybrid import hybrid_search
from services.api.deps import get_app_settings

router = APIRouter()


# Runs a hybrid precedent search, optionally filtered by clause type.
@router.get("")
def search(q: str, clause_type: str | None = None, settings: Settings = Depends(get_app_settings)) -> dict:
    hits = hybrid_search(settings, query=q, clause_type=clause_type)
    return {"query": q, "results": hits}
