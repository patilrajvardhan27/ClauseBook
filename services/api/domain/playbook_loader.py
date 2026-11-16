"""Loads a playbook's ladder from Postgres into the placement engine's plain
dataclasses. This is the one place that translates ORM rows to the engine's
input shape, used by both the preview endpoint and the worker's placement
stage, so the two never drift into different notions of "the ladder".
"""
from __future__ import annotations

import uuid

from clausebook_core.models.firm import Attribute
from clausebook_core.models.playbook import Position
from clausebook_core.placement.types import (
    AppliesWhenRule,
    AttributeSpec,
    Condition,
    Op,
    PositionSpec,
)
from sqlalchemy.orm import Session


def load_ladder(session: Session, playbook_id: uuid.UUID, clause_type_id: uuid.UUID) -> list[PositionSpec]:
    positions = (
        session.query(Position)
        .filter(Position.playbook_id == playbook_id, Position.clause_type_id == clause_type_id)
        .all()
    )
    return [_to_position_spec(p) for p in positions]


def _to_position_spec(position: Position) -> PositionSpec:
    conditions = [
        Condition(
            attribute_key=_attribute_key(c.attribute_id, position),
            op=Op(c.op),
            value=_condition_value(c.value_json),
        )
        for c in position.conditions
    ]
    applies_when = [
        AppliesWhenRule(key=r.key, op=Op(r.op), value=_condition_value(r.value_json))
        for r in position.applies_when
    ]
    return PositionSpec(
        id=str(position.id),
        rank=position.rank,
        label=position.label,
        is_walk_away=position.is_walk_away,
        conditions=conditions,
        applies_when=applies_when,
    )


def _attribute_key(attribute_id: uuid.UUID, position: Position) -> str:
    # position.conditions is eagerly joined to attribute in the repo query;
    # kept as a small lookup here rather than a second query per condition.
    for condition in position.conditions:
        if condition.attribute_id == attribute_id and condition.attribute is not None:
            return condition.attribute.key
    return str(attribute_id)


def _condition_value(value_json: dict):
    return value_json.get("value") if isinstance(value_json, dict) and "value" in value_json else value_json


def load_attribute_specs(session: Session, clause_type_id: uuid.UUID) -> dict[str, AttributeSpec]:
    attributes = session.query(Attribute).filter(Attribute.clause_type_id == clause_type_id).all()
    return {a.key: AttributeSpec(key=a.key, higher_is_better=a.higher_is_better) for a in attributes}
