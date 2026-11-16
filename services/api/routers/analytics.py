# Market stats and override rates; the math lives in ml/eval/market_stats.py.
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ml.eval.market_stats import clause_type_percentiles
from services.api.deps import get_db

router = APIRouter()


# Returns percentile stats for one clause type's attributes across the corpus.
@router.get("/market/{clause_type}")
def market_percentiles(clause_type: str, db: Session = Depends(get_db)) -> dict:
    return clause_type_percentiles(db, clause_type)


# Returns how often reviewers reject a proposed finding.
@router.get("/overrides")
def override_rates(db: Session = Depends(get_db)) -> dict:
    from clausebook_core.models.review import Finding

    total = db.query(Finding).filter(Finding.decision.isnot(None)).count()
    rejected = db.query(Finding).filter(Finding.decision == "rejected").count()
    return {"total_decided": total, "rejected": rejected, "override_rate": (rejected / total) if total else 0.0}
