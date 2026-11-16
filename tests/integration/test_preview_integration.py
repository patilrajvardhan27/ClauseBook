"""End-to-end check of the preview path against a real Postgres: seed a
clause type, a position and approved language, then confirm the preview
service extracts, ladders and proposes a fallback exactly as a lawyer
clicking "preview" in the playbook editor would see.

Requires CLAUSEBOOK_DATABASE_URL pointing at a migrated, empty-enough
database; CI provides one as a service container.
"""
from __future__ import annotations

import uuid

import pytest
from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.firm import Attribute, ClauseType, Firm
from clausebook_core.models.playbook import Playbook, Position, PositionCondition

from services.api.domain.preview_service import preview_placement

pytestmark = pytest.mark.integration


def test_preview_proposes_fallback_over_matched_position():
    settings = get_settings()
    factory = build_session_factory(settings)

    with session_scope(factory) as session:
        firm = Firm(name=f"integration-test-{uuid.uuid4()}")
        session.add(firm)
        session.flush()

        # Extractors are keyed by the exact CUAD category string, so this
        # reuses "Cap On Liability" rather than a randomized name -- and
        # reuses an existing row if a prior run left one behind, since the
        # column is unique.
        clause_type = session.query(ClauseType).filter(ClauseType.cuad_category == "Cap On Liability").one_or_none()
        if clause_type is None:
            clause_type = ClauseType(cuad_category="Cap On Liability", name="Cap On Liability")
            session.add(clause_type)
            session.flush()

        attribute = (
            session.query(Attribute)
            .filter(Attribute.clause_type_id == clause_type.id, Attribute.key == "cap_multiple")
            .one_or_none()
        )
        if attribute is None:
            attribute = Attribute(clause_type_id=clause_type.id, key="cap_multiple", kind="number", higher_is_better=False)
            session.add(attribute)
            session.flush()

        playbook = Playbook(firm_id=firm.id, name=f"integration-playbook-{uuid.uuid4()}", side="sell", version=1)
        session.add(playbook)
        session.flush()

        preferred = Position(playbook_id=playbook.id, clause_type_id=clause_type.id, rank=0, label="1x", is_walk_away=False)
        fallback = Position(playbook_id=playbook.id, clause_type_id=clause_type.id, rank=1, label="3x", is_walk_away=True)
        session.add_all([preferred, fallback])
        session.flush()

        session.add(PositionCondition(position_id=preferred.id, attribute_id=attribute.id, op="<=", value_json={"value": 1.0}))
        session.add(PositionCondition(position_id=fallback.id, attribute_id=attribute.id, op="<=", value_json={"value": 3.0}))
        session.flush()

        result = preview_placement(
            session,
            clause_text="Liability shall not exceed three (3) times the fees paid in the preceding twelve (12) months.",
            clause_type_id=clause_type.id,
            playbook_id=playbook.id,
            deal_context={},
        )

        assert result["attrs"]["cap_multiple"] == 3.0
        assert result["matched_position_id"] == str(fallback.id)
        assert result["proposed_position_id"] == str(preferred.id)
        assert not result["outside_playbook"]
