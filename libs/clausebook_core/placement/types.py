"""Plain data shapes the placement engine reads and returns.

Kept free of SQLAlchemy so the engine can be unit-tested with plain dicts
and reused from both the API's preview endpoint and the worker's review
pipeline without either one touching the database directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Op(str, Enum):
    LTE = "<="
    GTE = ">="
    EQ = "="
    IN = "in"
    CONTAINS_ALL = "contains_all"


@dataclass(frozen=True)
class Condition:
    attribute_key: str
    op: Op
    value: object


@dataclass(frozen=True)
class AppliesWhenRule:
    key: str
    op: Op
    value: object


@dataclass(frozen=True)
class PositionSpec:
    id: str
    rank: int
    label: str
    is_walk_away: bool
    conditions: list[Condition]
    applies_when: list[AppliesWhenRule] = field(default_factory=list)


@dataclass(frozen=True)
class AttributeSpec:
    key: str
    higher_is_better: bool


@dataclass
class PlacementResult:
    matched_position_id: str | None
    proposed_position_id: str | None
    outside_playbook: bool
    reason: str
    better_attributes: list[str] = field(default_factory=list)
