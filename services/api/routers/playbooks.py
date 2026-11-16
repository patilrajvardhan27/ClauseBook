# Playbook CRUD; publishing bumps the version instead of mutating rows in place.
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from clausebook_core.models.playbook import Playbook
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.api.deps import get_db
from services.api.domain.preview_service import preview_placement
from services.api.schemas import PlaybookOut, PreviewRequest, PreviewResponse

router = APIRouter()


# Lists every playbook.
@router.get("", response_model=list[PlaybookOut])
def list_playbooks(db: Session = Depends(get_db)) -> list[Playbook]:
    return db.query(Playbook).all()


# Creates a new playbook at version 1.
@router.post("", status_code=201, response_model=PlaybookOut)
def create_playbook(name: str, side: str, firm_id: uuid.UUID, db: Session = Depends(get_db)) -> Playbook:
    playbook = Playbook(firm_id=firm_id, name=name, side=side, version=1)
    db.add(playbook)
    db.flush()
    return playbook


# Bumps a playbook's version and stamps its publish time.
@router.post("/{playbook_id}/publish", response_model=PlaybookOut)
def publish_playbook(playbook_id: uuid.UUID, db: Session = Depends(get_db)) -> Playbook:
    playbook = db.get(Playbook, playbook_id)
    playbook.version += 1
    playbook.published_at = datetime.now(UTC)
    db.flush()
    return playbook


# Places a pasted clause against a playbook with no document or review behind it.
@router.post("/{playbook_id}/preview", response_model=PreviewResponse)
def preview(playbook_id: uuid.UUID, payload: PreviewRequest, db: Session = Depends(get_db)) -> dict:
    return preview_placement(
        db, payload.clause_text, payload.clause_type_id, playbook_id, payload.deal_context.model_dump()
    )
