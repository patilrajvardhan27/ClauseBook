# Upload a contract; dedupe by content hash so re-uploading never makes a second document.
from __future__ import annotations

import hashlib
import uuid

from clausebook_core.models.document import Document
from clausebook_core.models.firm import Firm
from clausebook_core.storage.local_blob_store import write_blob
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from services.api.deps import get_db
from services.api.schemas import DocumentOut

router = APIRouter()

# Firm comes from the authenticated session once auth/ is wired to a real
# identity provider; pinned to a single dev firm for this slice.
DEV_FIRM_ID = uuid.UUID(int=0)
DEV_FIRM_NAME = "Dev firm (no auth wired in this slice)"


# Finds or creates the fixed dev firm this slice uploads every document under.
def _get_or_create_dev_firm(db: Session) -> Firm:
    firm = db.get(Firm, DEV_FIRM_ID)
    if firm is None:
        firm = Firm(id=DEV_FIRM_ID, name=DEV_FIRM_NAME)
        db.add(firm)
        db.flush()
    return firm


# Uploads a document, returning the existing row if its hash already exists.
@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> Document:
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    write_blob(sha256, file.filename or "untitled", content)

    existing = db.query(Document).filter(Document.sha256 == sha256).one_or_none()
    if existing:
        return existing

    firm = _get_or_create_dev_firm(db)
    document = Document(firm_id=firm.id, sha256=sha256, title=file.filename or "untitled", pages=0)
    db.add(document)
    db.flush()
    return document


# Fetches one document by id.
@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> Document:
    return db.get(Document, document_id)
