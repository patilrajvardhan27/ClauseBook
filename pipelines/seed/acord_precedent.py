# Seeds ACORD's own corpus into Postgres as precedent, outbox-only, same as pipelines/seed/cuad_precedent.py.
from __future__ import annotations

from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.job import OutboxEvent
from clausebook_core.models.playbook import Precedent

from pipelines.bronze.acord import download, extract_acord


# Writes one ACORD corpus clause as a precedent row plus its outbox event; skips if already seeded.
def _seed_one_clause(session, acord_id: str, text: str) -> bool:
    document_id = f"acord:{acord_id}"
    existing = session.query(Precedent).filter(Precedent.document_id == document_id).one_or_none()
    if existing is not None:
        return False

    precedent = Precedent(
        firm_id=None,
        source="acord",
        document_id=document_id,
        clause_text=text,
        clause_type_id=None,
        position_id=None,
        attrs_json={},
    )
    session.add(precedent)
    session.flush()

    session.add(
        OutboxEvent(
            aggregate="precedent",
            type="precedent_upserted",
            payload_json={"id": str(precedent.id), "clause_text": text, "document_id": document_id, "source": "acord"},
        )
    )
    return True


# Seeds every ACORD corpus clause as precedent.
def seed_acord_precedent() -> int:
    archive_path = download()
    data = extract_acord(archive_path)

    settings = get_settings()
    factory = build_session_factory(settings)
    seeded = 0

    with session_scope(factory) as session:
        for entry in data["corpus"]:
            if _seed_one_clause(session, entry["_id"], entry["text"]):
                seeded += 1

    print(f"Seeded {seeded} new ACORD precedent rows")
    return seeded


if __name__ == "__main__":
    seed_acord_precedent()
