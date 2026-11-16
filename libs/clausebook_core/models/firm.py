"""Tenant boundary and the vocabulary every firm shares.

A firm's playbook, positions and precedent all carry firm_id so Postgres
row-level security can enforce isolation at the database layer, not just in
application code that a future engineer might forget to check.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clausebook_core.models.base import Base, UUIDPk


class Firm(Base, UUIDPk):
    __tablename__ = "firm"

    name: Mapped[str] = mapped_column(String(200), unique=True)

    playbooks: Mapped[list["Playbook"]] = relationship(back_populates="firm")


class ClauseType(Base, UUIDPk):
    """Shared vocabulary mapped to CUAD categories, so training data and a
    firm's own guidance meet on one key instead of two parallel taxonomies."""

    __tablename__ = "clause_type"

    cuad_category: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))

    attributes: Mapped[list["Attribute"]] = relationship(back_populates="clause_type")


class Attribute(Base, UUIDPk):
    """The measurable part of a clause type. Comparing a cap multiple by rule
    is reliable; comparing the surrounding prose by similarity is not."""

    __tablename__ = "attribute"

    clause_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clause_type.id"))
    key: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))  # number | enum | bool | list
    # Which direction counts as "better" for the side the playbook is written for.
    # Flipped by Position.applies to the other side's perspective at placement time.
    higher_is_better: Mapped[bool] = mapped_column(default=True)

    clause_type: Mapped[ClauseType] = relationship(back_populates="attributes")

