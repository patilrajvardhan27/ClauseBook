# Writes CUAD gold segments into Postgres as precedent rows, with an outbox event per row.
#
# This is the only way precedent reaches OpenSearch: write to Postgres,
# let services/worker/outbox.py relay it. No direct bulk-load path exists
# on purpose, so the index stays provably rebuildable from Postgres (ADR 2).
#
# Usage: PYTHONPATH=.:libs python3 pipelines/seed/cuad_precedent.py
from __future__ import annotations

import csv
import json
from pathlib import Path

from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.firm import ClauseType
from clausebook_core.models.job import OutboxEvent
from clausebook_core.models.playbook import Precedent

from ml.extract.extractors import extract

GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")


# Finds or creates the clause type for a CUAD category.
def _get_or_create_clause_type(session, cuad_category: str) -> ClauseType:
    clause_type = session.query(ClauseType).filter(ClauseType.cuad_category == cuad_category).one_or_none()
    if clause_type is None:
        clause_type = ClauseType(cuad_category=cuad_category, name=cuad_category)
        session.add(clause_type)
        session.flush()
    return clause_type


# Writes one precedent row plus its outbox event; skips a segment already seeded by document_id.
def _seed_one_segment(session, contract_id: str, ord_: int, text: str, category: str) -> bool:
    document_id = f"{contract_id}#{ord_}"
    existing = session.query(Precedent).filter(Precedent.document_id == document_id).one_or_none()
    if existing is not None:
        return False

    clause_type = _get_or_create_clause_type(session, category)
    attrs = extract(category, text)

    precedent = Precedent(
        firm_id=None,
        source="cuad",
        document_id=document_id,
        clause_text=text,
        clause_type_id=clause_type.id,
        position_id=None,
        attrs_json=attrs,
    )
    session.add(precedent)
    session.flush()

    session.add(
        OutboxEvent(
            aggregate="precedent",
            type="precedent_upserted",
            payload_json={
                "id": str(precedent.id),
                "clause_text": text,
                "clause_type": category,
                "document_id": document_id,
                "source": "cuad",
            },
        )
    )
    return True


# Reads every gold segment and seeds it as precedent, skipping rows already seeded.
def seed_cuad_precedent() -> int:
    if not GOLD_SEGMENTS_PATH.exists():
        raise FileNotFoundError(f"{GOLD_SEGMENTS_PATH} not found; run pipelines/gold/run_gold.py first")

    settings = get_settings()
    factory = build_session_factory(settings)
    seeded = 0

    with GOLD_SEGMENTS_PATH.open() as f, session_scope(factory) as session:
        for row in csv.DictReader(f):
            categories = json.loads(row["categories_json"])
            for category in categories:
                if _seed_one_segment(session, row["contract_id"], int(row["ord"]), row["text"], category):
                    seeded += 1

    print(f"Seeded {seeded} new precedent rows from {GOLD_SEGMENTS_PATH}")
    print("Run the worker (or relay_pending_events directly) to push them into OpenSearch.")
    return seeded


if __name__ == "__main__":
    seed_cuad_precedent()
