"""Pydantic request/response models. The OpenAPI spec in contracts/openapi
is generated from these, so the TypeScript client and this API never drift
against each other.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response models read straight off a SQLAlchemy row."""

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(ORMModel):
    id: uuid.UUID
    title: str
    pages: int
    sha256: str
    uploaded_at: datetime


class PlaybookOut(ORMModel):
    id: uuid.UUID
    firm_id: uuid.UUID
    name: str
    side: str
    version: int
    published_at: datetime | None


class DealContext(BaseModel):
    party_role: str | None = None
    deal_size_band: str | None = None
    counterparty_type: str | None = None


class ReviewCreate(BaseModel):
    document_id: uuid.UUID
    playbook_id: uuid.UUID
    deal_context: DealContext = DealContext()


class ReviewOut(ORMModel):
    id: uuid.UUID
    document_id: uuid.UUID
    playbook_id: uuid.UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None


class FindingOut(ORMModel):
    id: uuid.UUID
    segment_id: uuid.UUID
    clause_type_id: uuid.UUID | None
    confidence: float
    attrs: dict
    matched_position_id: uuid.UUID | None
    proposed_position_id: uuid.UUID | None
    redline: dict
    evidence: dict
    decision: str | None


class FindingPatch(BaseModel):
    decision: str  # accepted | rejected | edited
    reason: str | None = None
    edited_text: str | None = None


class PreviewRequest(BaseModel):
    clause_text: str
    clause_type_id: uuid.UUID
    deal_context: DealContext = DealContext()


class PreviewResponse(BaseModel):
    attrs: dict
    matched_position_id: uuid.UUID | None
    proposed_position_id: uuid.UUID | None
    outside_playbook: bool
    reason: str
