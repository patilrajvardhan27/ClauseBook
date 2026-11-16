# The ordered ladder of positions a firm will accept for a clause type.
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clausebook_core.models.base import Base, UUIDPk


# A versioned, side-specific set of positions; a past review stays pinned to its version.
class Playbook(Base, UUIDPk):
    __tablename__ = "playbook"

    firm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("firm.id"))
    name: Mapped[str] = mapped_column(String(200))
    side: Mapped[str] = mapped_column(String(20))  # buy | sell
    version: Mapped[int] = mapped_column(Integer, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    firm = relationship("Firm", back_populates="playbooks")
    positions: Mapped[list[Position]] = relationship(back_populates="playbook")


# One ranked stance on a clause type: rank 0 is preferred, the last rank is the walk-away.
class Position(Base, UUIDPk):
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


# What the extracted attributes must satisfy for a clause to sit at this position.
class PositionCondition(Base, UUIDPk):
    __tablename__ = "position_condition"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    attribute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attribute.id"))
    op: Mapped[str] = mapped_column(String(20))  # <=, >=, =, in, contains_all
    value_json: Mapped[dict] = mapped_column(JSONB)

    position = relationship("Position", back_populates="conditions")
    attribute = relationship("Attribute")


# Deal context that switches a position on or off: party role, deal size, counterparty type.
class AppliesWhen(Base, UUIDPk):
    __tablename__ = "applies_when"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    key: Mapped[str] = mapped_column(String(80))
    op: Mapped[str] = mapped_column(String(20))
    value_json: Mapped[dict] = mapped_column(JSONB)

    position = relationship("Position", back_populates="applies_when")


# Text a lawyer may insert for a position; a position can hold several variants.
class ApprovedLanguage(Base, UUIDPk):
    __tablename__ = "approved_language"

    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("position.id"))
    text: Mapped[str] = mapped_column(String)
    source_note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    position = relationship("Position", back_populates="approved_language")


# A real clause instance linked to the position it satisfies.
class Precedent(Base, UUIDPk):
    __tablename__ = "precedent"

    firm_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("firm.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(50))  # cuad | firm | acord
    document_id: Mapped[str] = mapped_column(String(200))
    clause_text: Mapped[str] = mapped_column(String)
    # Nullable because a retrieval-only corpus (ACORD) has no single CUAD category per clause;
    # CUAD-derived precedent always sets this.
    clause_type_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clause_type.id"), nullable=True)
    position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("position.id"), nullable=True)
    attrs_json: Mapped[dict] = mapped_column(JSONB, default=dict)
