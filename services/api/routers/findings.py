"""Accept, reject or edit a proposed fallback.

A reject writes a reason that feeds the rejected-position history (section
4.3): the placement engine never re-proposes a position this counterparty
has already turned down in the same document family.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from clausebook_core.models.review import Finding
from services.api.deps import get_db
from services.api.schemas import FindingOut, FindingPatch

router = APIRouter()


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: uuid.UUID, db: Session = Depends(get_db)) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return _to_out(finding)


@router.patch("/{finding_id}", response_model=FindingOut)
def decide_finding(finding_id: uuid.UUID, patch: FindingPatch, db: Session = Depends(get_db)) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.decision = patch.decision
    if patch.decision == "rejected" and patch.reason:
        finding.evidence_json = {**finding.evidence_json, "rejection_reason": patch.reason}
    if patch.decision == "edited" and patch.edited_text:
        finding.redline_json = {**finding.redline_json, "final_text": patch.edited_text}

    db.flush()
    return _to_out(finding)


def _to_out(finding: Finding) -> dict:
    return {
        "id": finding.id,
        "segment_id": finding.segment_id,
        "clause_type_id": finding.clause_type_id,
        "confidence": finding.confidence,
        "attrs": finding.attrs_json,
        "matched_position_id": finding.matched_position_id,
        "proposed_position_id": finding.proposed_position_id,
        "redline": finding.redline_json,
        "evidence": finding.evidence_json,
        "decision": finding.decision,
    }
