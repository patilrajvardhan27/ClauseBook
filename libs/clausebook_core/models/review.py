"""One run over one document, and the per-clause result of that run.

finding.evidence_json carries the retrieved precedent ids, the extracted
attribute spans and the rule results that led to a decision, so every
proposal in the add-in traces back to something checkable.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from clausebook_core.models.base import Base, UUIDPk


class Review(Base, UUIDPk):
    __tablename__ = "review"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document.id"))
    playbook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playbook.id"))
    playbook_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cost_tokens: Mapped[int] = mapped_column(Integer, default=0)


class Finding(Base, UUIDPk):
    __tablename__ = "finding"

    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review.id"))
    segment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("segment.id"))
    clause_type_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clause_type.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    attrs_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    matched_position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("position.id"), nullable=True)
    proposed_position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("position.id"), nullable=True)
    redline_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)  # accepted | rejected | edited
    decided_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
