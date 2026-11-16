"""Rule evaluation: does a set of extracted attributes satisfy a condition.

This is deliberately the dumbest code in the project. Fallback accuracy
comes from getting the extraction right and the ladder right, not from a
clever comparator. A clever comparator is also a comparator nobody can
audit, and auditability is the point of comparing by rule in the first
place.
"""
from __future__ import annotations

from collections.abc import Iterable

from clausebook_core.placement.types import Condition, Op


def check_condition(condition: Condition, attrs: dict) -> bool:
    actual = attrs.get(condition.attribute_key)
    if actual is None:
        return False  # an attribute we could not extract never satisfies a condition

    match condition.op:
        case Op.LTE:
            return actual <= condition.value
        case Op.GTE:
            return actual >= condition.value
        case Op.EQ:
            return actual == condition.value
        case Op.IN:
            allowed = condition.value
            if not isinstance(allowed, Iterable):
                raise TypeError(f"'in' needs an iterable value, got {type(allowed).__name__}")
            return actual in allowed
        case Op.CONTAINS_ALL:
            required, actual_values = condition.value, actual
            if not isinstance(required, Iterable) or not isinstance(actual_values, Iterable):
                raise TypeError("'contains_all' needs an iterable condition value and attribute value")
            return set(required).issubset(set(actual_values))
        case _:
            raise ValueError(f"Unknown operator: {condition.op}")


def all_conditions_pass(conditions: list[Condition], attrs: dict) -> bool:
    return all(check_condition(c, attrs) for c in conditions)


def applies_to_context(rules: list, deal_context: dict) -> bool:
    """A position with no applies_when rules is unconditional. Any rule that
    fails rules the position out for this deal."""
    for rule in rules:
        actual = deal_context.get(rule.key)
        condition = Condition(attribute_key=rule.key, op=rule.op, value=rule.value)
        if not check_condition(condition, {rule.key: actual}):
            return False
    return True
