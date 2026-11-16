# The ranking algorithm that decides what to propose for a clause.
from __future__ import annotations

from clausebook_core.placement.conditions import all_conditions_pass, applies_to_context
from clausebook_core.placement.types import AttributeSpec, PlacementResult, PositionSpec


# Ranks a clause against its playbook ladder and decides what to propose.
def place(
    attrs: dict,
    ladder: list[PositionSpec],
    deal_context: dict,
    attribute_specs: dict[str, AttributeSpec],
    rejected_position_ids: set[str] | None = None,
) -> PlacementResult:
    rejected_position_ids = rejected_position_ids or set()

    live_ladder = [p for p in ladder if applies_to_context(p.applies_when, deal_context)]
    live_ladder = sorted(live_ladder, key=lambda p: p.rank)

    matched = _first_satisfied(live_ladder, attrs)

    if matched is None:
        walk_away = next((p for p in live_ladder if p.is_walk_away), None)
        return PlacementResult(
            matched_position_id=None,
            proposed_position_id=walk_away.id if walk_away else None,
            outside_playbook=True,
            reason="No position in the playbook accepts these terms; this sits past the walk-away line.",
        )

    if matched.rank == 0:
        return PlacementResult(
            matched_position_id=matched.id,
            proposed_position_id=None,
            outside_playbook=False,
            reason="Clause already sits at the preferred position. No change needed.",
        )

    target, better_on = _best_unrejected_improvement(live_ladder, matched, attrs, attribute_specs, rejected_position_ids)
    if target is None:
        # Everything better than the current match has already been rejected by this
        # counterparty in this negotiation; holding the matched position is the live option.
        return PlacementResult(
            matched_position_id=matched.id,
            proposed_position_id=matched.id,
            outside_playbook=False,
            reason="Every stronger position has already been rejected in this negotiation; holding here.",
        )

    return PlacementResult(
        matched_position_id=matched.id,
        proposed_position_id=target.id,
        outside_playbook=False,
        reason=f"Proposing fallback '{target.label}', the best unrejected position ahead of the current match.",
        better_attributes=better_on,
    )


# Finds where the counterparty's text sits today: the first position whose conditions all pass.
def _first_satisfied(ladder: list[PositionSpec], attrs: dict) -> PositionSpec | None:
    for position in ladder:
        if all_conditions_pass(position.conditions, attrs):
            return position
    return None


# Finds the lowest-rank unrejected position that beats the matched one on at least one attribute.
def _best_unrejected_improvement(
    ladder: list[PositionSpec],
    matched: PositionSpec,
    attrs: dict,
    attribute_specs: dict[str, AttributeSpec],
    rejected_position_ids: set[str],
) -> tuple[PositionSpec | None, list[str]]:
    candidates = [p for p in ladder if p.rank < matched.rank and p.id not in rejected_position_ids]
    candidates.sort(key=lambda p: p.rank)

    for candidate in candidates:
        better_on = _strictly_better_attributes(candidate, matched, attrs, attribute_specs)
        if better_on:
            return candidate, better_on

    return None, []


# Compares candidate and matched conditions by attribute key and declared direction, not text similarity.
def _strictly_better_attributes(
    candidate: PositionSpec, matched: PositionSpec, attrs: dict, attribute_specs: dict[str, AttributeSpec]
) -> list[str]:
    better: list[str] = []
    matched_by_key = {c.attribute_key: c for c in matched.conditions}

    for condition in candidate.conditions:
        spec = attribute_specs.get(condition.attribute_key)
        other = matched_by_key.get(condition.attribute_key)
        if spec is None or other is None or not isinstance(condition.value, (int, float)):
            continue
        if not isinstance(other.value, (int, float)):
            continue
        is_better = condition.value > other.value if spec.higher_is_better else condition.value < other.value
        if is_better:
            better.append(condition.attribute_key)

    return better
