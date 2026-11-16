# Plain data shapes the placement engine reads and returns, free of SQLAlchemy.
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# A condition's comparison operator.
class Op(str, Enum):
    LTE = "<="
    GTE = ">="
    EQ = "="
    IN = "in"
    CONTAINS_ALL = "contains_all"


# One rule an attribute must satisfy for a position to match.
@dataclass(frozen=True)
class Condition:
    attribute_key: str
    op: Op
    value: object


# One rule that switches a position on or off for a given deal context.
@dataclass(frozen=True)
class AppliesWhenRule:
    key: str
    op: Op
    value: object


# One rung on a playbook's ladder, with its conditions and context rules.
@dataclass(frozen=True)
class PositionSpec:
    id: str
    rank: int
    label: str
    is_walk_away: bool
    conditions: list[Condition]
    applies_when: list[AppliesWhenRule] = field(default_factory=list)


# An attribute's key and which direction counts as better.
@dataclass(frozen=True)
class AttributeSpec:
    key: str
    higher_is_better: bool


# What place() decided for one clause.
@dataclass
class PlacementResult:
    matched_position_id: str | None
    proposed_position_id: str | None
    outside_playbook: bool
    reason: str
    better_attributes: list[str] = field(default_factory=list)
