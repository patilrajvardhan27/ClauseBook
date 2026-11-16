# Unit tests for the core placement algorithm; no database or API key needed.
from clausebook_core.placement.engine import place
from clausebook_core.placement.types import AttributeSpec, Condition, Op, PositionSpec

CAP_MULTIPLE = AttributeSpec(key="cap_multiple", higher_is_better=False)  # lower cap is better for the buy side
ATTRS = {"cap_multiple": CAP_MULTIPLE}


# Builds a ladder of positions, one per cap-multiple value, with the last rank as walk-away.
def ladder_with_ranks(values: list[float]) -> list[PositionSpec]:
    return [
        PositionSpec(
            id=f"pos-{i}",
            rank=i,
            label=f"rank {i}",
            is_walk_away=(i == len(values) - 1),
            conditions=[Condition("cap_multiple", Op.LTE, v)],
        )
        for i, v in enumerate(values)
    ]


# A clause already at rank 0 needs no change.
def test_preferred_position_needs_no_change():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    result = place({"cap_multiple": 1.0}, ladder, {}, ATTRS)
    assert result.matched_position_id == "pos-0"
    assert result.proposed_position_id is None
    assert not result.outside_playbook


# A clause at a worse rank gets the preferred position proposed as the fallback.
def test_fallback_is_proposed_over_matched_position():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    result = place({"cap_multiple": 3.0}, ladder, {}, ATTRS)
    assert result.matched_position_id == "pos-2"
    assert result.proposed_position_id == "pos-0"
    assert result.better_attributes == ["cap_multiple"]


# A clause worse than every position flags outside_playbook and proposes the walk-away.
def test_text_outside_every_position_flags_walk_away():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    result = place({"cap_multiple": 10.0}, ladder, {}, ATTRS)
    assert result.outside_playbook
    assert result.matched_position_id is None
    assert result.proposed_position_id == "pos-2"


# A previously rejected position is skipped in favor of the next best one.
def test_rejected_positions_are_not_reproposed():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    result = place({"cap_multiple": 3.0}, ladder, {}, ATTRS, rejected_position_ids={"pos-0"})
    assert result.proposed_position_id == "pos-1"


# When every stronger position has been rejected, the engine holds the current match.
def test_everything_better_already_rejected_holds_current_match():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    result = place(
        {"cap_multiple": 3.0}, ladder, {}, ATTRS, rejected_position_ids={"pos-0", "pos-1"}
    )
    assert result.proposed_position_id == "pos-2"
    assert result.matched_position_id == "pos-2"


# A position whose applies_when rule fails drops out of the ladder for that deal.
def test_applies_when_removes_a_position_from_the_ladder():
    ladder = ladder_with_ranks([1.0, 2.0, 3.0])
    from clausebook_core.placement.types import AppliesWhenRule

    # Pretend rank 0 only applies to small deals; this deal is large, so rank 0 drops out.
    ladder[0] = PositionSpec(
        id="pos-0", rank=0, label="rank 0", is_walk_away=False,
        conditions=ladder[0].conditions,
        applies_when=[AppliesWhenRule(key="deal_size_band", op=Op.EQ, value="small")],
    )
    result = place({"cap_multiple": 1.0}, ladder, {"deal_size_band": "large"}, ATTRS)
    assert result.matched_position_id == "pos-1"
