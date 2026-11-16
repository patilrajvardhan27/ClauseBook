"""Upload a contract; dedupe by content hash so re-uploading the same file
never creates a second document or a second review history for it."""
from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from clausebook_core.models.document import Document
from services.api.deps import get_db
from services.api.schemas import DocumentOut

router = APIRouter()

# Firm comes from the authenticated session once auth/ is wired to a real
# identity provider; pinned to a single dev firm for this slice.
DEV_FIRM_ID = uuid.UUID(int=0)


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> Document:
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    existing = db.query(Document).filter(Document.sha256 == sha256).one_or_none()
    if existing:
        return existing

    document = Document(firm_id=DEV_FIRM_ID, sha256=sha256, title=file.filename or "untitled", pages=0)
    db.add(document)
    db.flush()
    return document


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> Document:
    return db.get(Document, document_id)
