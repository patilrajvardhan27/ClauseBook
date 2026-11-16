"""Writes the eight clause types, their attributes and the sample playbook
onto a fresh database. Idempotent: re-running finds existing rows by their
natural key (cuad_category, attribute key, playbook name) and updates
rather than duplicates them.

Usage: PYTHONPATH=.:libs python3 pipelines/seed/run_seed.py
"""
from __future__ import annotations

from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.firm import Attribute, ClauseType, Firm
from clausebook_core.models.playbook import ApprovedLanguage, Playbook, Position, PositionCondition

from pipelines.seed.sample_playbooks import SAMPLE_LADDERS

SAMPLE_FIRM_NAME = "Sample Firm (not a real firm -- public drafting guidance only)"
SAMPLE_PLAYBOOK_NAME = "Sample Sell-Side SaaS Playbook"


def seed() -> None:
    settings = get_settings()
    factory = build_session_factory(settings)

    with session_scope(factory) as session:
        firm = _get_or_create_firm(session)
        playbook = _get_or_create_playbook(session, firm.id)

        for cuad_category, attr_key, attr_kind, higher_is_better, rungs in SAMPLE_LADDERS:
            clause_type = _get_or_create_clause_type(session, cuad_category)
            attribute = _get_or_create_attribute(session, clause_type.id, attr_key, attr_kind, higher_is_better)
            _replace_positions(session, playbook.id, clause_type.id, attribute.id, rungs)

        print(f"Seeded playbook '{playbook.name}' with {len(SAMPLE_LADDERS)} clause-type ladders.")


def _get_or_create_firm(session) -> Firm:
    firm = session.query(Firm).filter(Firm.name == SAMPLE_FIRM_NAME).one_or_none()
    if firm is None:
        firm = Firm(name=SAMPLE_FIRM_NAME)
        session.add(firm)
        session.flush()
    return firm


def _get_or_create_playbook(session, firm_id) -> Playbook:
    playbook = session.query(Playbook).filter(Playbook.name == SAMPLE_PLAYBOOK_NAME).one_or_none()
    if playbook is None:
        playbook = Playbook(firm_id=firm_id, name=SAMPLE_PLAYBOOK_NAME, side="sell", version=1)
        session.add(playbook)
        session.flush()
    return playbook


def _get_or_create_clause_type(session, cuad_category: str) -> ClauseType:
    clause_type = session.query(ClauseType).filter(ClauseType.cuad_category == cuad_category).one_or_none()
    if clause_type is None:
        clause_type = ClauseType(cuad_category=cuad_category, name=cuad_category)
        session.add(clause_type)
        session.flush()
    return clause_type


def _get_or_create_attribute(session, clause_type_id, key, kind, higher_is_better) -> Attribute:
    attribute = (
        session.query(Attribute)
        .filter(Attribute.clause_type_id == clause_type_id, Attribute.key == key)
        .one_or_none()
    )
    if attribute is None:
        attribute = Attribute(clause_type_id=clause_type_id, key=key, kind=kind, higher_is_better=higher_is_better)
        session.add(attribute)
        session.flush()
    return attribute


def _replace_positions(session, playbook_id, clause_type_id, attribute_id, rungs) -> None:
    existing = (
        session.query(Position)
        .filter(Position.playbook_id == playbook_id, Position.clause_type_id == clause_type_id)
        .all()
    )
    for position in existing:
        session.delete(position)
    session.flush()

    for rank, label, is_walk_away, op, value, approved_text in rungs:
        position = Position(
            playbook_id=playbook_id, clause_type_id=clause_type_id, rank=rank, label=label, is_walk_away=is_walk_away
        )
        session.add(position)
        session.flush()
        session.add(PositionCondition(position_id=position.id, attribute_id=attribute_id, op=op, value_json={"value": value}))
        session.add(ApprovedLanguage(position_id=position.id, text=approved_text, source_note="Sample playbook: public drafting guidance"))


if __name__ == "__main__":
    seed()
