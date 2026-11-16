# A Postgres-backed job queue and an outbox for OpenSearch indexing.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from clausebook_core.models.base import Base, UUIDPk, utcnow


# One queued unit of work, claimed with FOR UPDATE SKIP LOCKED.
class Job(Base, UUIDPk):
    __tablename__ = "job"

    kind: Mapped[str] = mapped_column(String(50))
    payload_json: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# An unpublished change waiting to be relayed into OpenSearch.
class OutboxEvent(Base, UUIDPk):
    __tablename__ = "outbox_event"

    aggregate: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
