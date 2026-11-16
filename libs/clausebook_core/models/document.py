# An uploaded contract and the segments it gets split into.
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from clausebook_core.models.base import Base, UUIDPk, utcnow


# An uploaded contract, deduped by content hash.
class Document(Base, UUIDPk):
    __tablename__ = "document"

    firm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("firm.id"))
    sha256: Mapped[str] = mapped_column(String(64), unique=True)  # dedupe on re-upload
    title: Mapped[str] = mapped_column(String(300))
    pages: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# One clause-sized span of a document's text, in reading order.
class Segment(Base, UUIDPk):
    __tablename__ = "segment"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document.id"))
    ord: Mapped[int] = mapped_column(Integer)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String)
    heading: Mapped[str | None] = mapped_column(String(300), nullable=True)
