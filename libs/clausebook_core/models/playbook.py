"""The ordered ladder of positions a firm will accept for a clause type.

A playbook can be versioned and a firm can hold several (buy side, sell
side, by practice group), because guidance changes over time and a past
review has to stay explainable against the version it actually ran on.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clausebook_core.models.base import Base, UUIDPk


class Playbook(Base, UUIDPk):
    __tablename__ = "playbook"

    firm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("firm.id"))
    name: Mapped[str] = mapped_column(String(200))
    side: Mapped[str] = mapped_column(String(20))  # buy | sell
    version: Mapped[int] = mapped_column(Integer, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    firm = relationship("Firm", back_populates="playbooks")
    positions: Mapped[list[Position]] = relationship(back_populates="playbook")


class Position(Base, UUIDPk):
    """One ordered stance on a clause type. Rank 0 is preferred language,
    the last rank is the walk-away. Ordering is what makes fallback choice a
    ranking problem rather than a retrieval problem: retrieval only finds
    evidence, the rank decides what gets proposed."""

    __tablename__ = "position"

    playbook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playbook.id"))
    clause_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clause_type.id"))
    rank: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(200))
    is_walk_away: Mapped[bool] = mapped_column(Boolean, default=False)

    playbook = relationship("Playbook", back_populates="positions")
    conditions: Mapped[list[PositionCondition]] = relationship(back_populates="position")
    applies_when: Mapped[list[AppliesWhen]] = relationship(back_populates="position")
    approved_language: Mapped[list[ApprovedLanguage]] = relationship(back_populates="position")


class PositionCondition(Base, UUIDPk):
    """What the extracted attributes must satisfy for a clause to count as
    sitting at this position. Stored as data so a condition can change
    without a code deploy."""

    __tablename__ = "position_condition"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    attribute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attribute.id"))
    op: Mapped[str] = mapped_column(String(20))  # <=, >=, =, in, contains_all
    value_json: Mapped[dict] = mapped_column(JSONB)

    position = relationship("Position", back_populates="conditions")
    attribute = relationship("Attribute")


class AppliesWhen(Base, UUIDPk):
    """Deal context that switches a position on or off: party role, deal
    size band, counterparty type. Most playbook tools skip this and treat
    guidance as context-free, which is where they go wrong on real deals."""

    __tablename__ = "applies_when"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    key: Mapped[str] = mapped_column(String(80))
    op: Mapped[str] = mapped_column(String(20))
    value_json: Mapped[dict] = mapped_column(JSONB)

    position = relationship("Position", back_populates="applies_when")


class ApprovedLanguage(Base, UUIDPk):
    """The text a lawyer may actually insert for a position. A position can
    hold several variants, each with a note on where it came from."""

    __tablename__ = "approved_language"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    text: Mapped[str] = mapped_column(String)
    source_note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    position = relationship("Position", back_populates="approved_language")


class Precedent(Base, UUIDPk):
    """A real clause instance linked to the position it satisfies, so a
    proposal can say 'we accepted this before, in deal X' rather than just
    'this text is similar'."""

    __tablename__ = "precedent"

    firm_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("firm.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(50))  # cuad | firm
    document_id: Mapped[str] = mapped_column(String(200))
    clause_text: Mapped[str] = mapped_column(String)
    clause_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clause_type.id"))
    position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("position.id"), nullable=True)
    attrs_json: Mapped[dict] = mapped_column(JSONB, default=dict)
