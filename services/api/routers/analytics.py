"""Market stats and override rates, computed from the corpus and from
finding decisions respectively. Kept thin -- the actual math lives in
ml/eval/market_stats.py so a pandas test can check it directly."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ml.eval.market_stats import clause_type_percentiles
from services.api.deps import get_db

router = APIRouter()


@router.get("/market/{clause_type}")
def market_percentiles(clause_type: str, db: Session = Depends(get_db)) -> dict:
    return clause_type_percentiles(db, clause_type)


@router.get("/overrides")
def override_rates(db: Session = Depends(get_db)) -> dict:
    from clausebook_core.models.review import Finding

    total = db.query(Finding).filter(Finding.decision.isnot(None)).count()
    rejected = db.query(Finding).filter(Finding.decision == "rejected").count()
    return {"total_decided": total, "rejected": rejected, "override_rate": (rejected / total) if total else 0.0}
