# Tenant boundary (Firm) and the clause-type vocabulary every firm shares.
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clausebook_core.models.base import Base, UUIDPk

if TYPE_CHECKING:
    from clausebook_core.models.playbook import Playbook


# A firm, scoped by firm_id everywhere row-level security applies.
class Firm(Base, UUIDPk):
    __tablename__ = "firm"

    name: Mapped[str] = mapped_column(String(200), unique=True)

    playbooks: Mapped[list[Playbook]] = relationship(back_populates="firm")


# A clause category shared between CUAD's taxonomy and a firm's own guidance.
class ClauseType(Base, UUIDPk):
    __tablename__ = "clause_type"

    cuad_category: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))

    attributes: Mapped[list[Attribute]] = relationship(back_populates="clause_type")


# A measurable term on a clause type, compared by rule rather than by text similarity.
class Attribute(Base, UUIDPk):
    __tablename__ = "attribute"

    clause_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clause_type.id"))
    key: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))  # number | enum | bool | list
    # Which direction counts as "better" for the side the playbook is written for.
    # Flipped by Position.applies to the other side's perspective at placement time.
    higher_is_better: Mapped[bool] = mapped_column(default=True)

    clause_type: Mapped[ClauseType] = relationship(back_populates="attributes")

