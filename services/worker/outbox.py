# Relays outbox rows into OpenSearch; Postgres stays the source of truth (see ADR 2).
from __future__ import annotations

from datetime import UTC

from clausebook_core.config.settings import Settings
from clausebook_core.models.job import OutboxEvent
from sqlalchemy import select
from sqlalchemy.orm import Session


# Indexes every unpublished outbox event into OpenSearch and marks it published.
def relay_pending_events(session: Session, settings: Settings, batch_size: int = 100) -> int:
    try:
        from opensearchpy import OpenSearch, helpers
    except ImportError:
        return 0

    stmt = select(OutboxEvent).where(OutboxEvent.published_at.is_(None)).limit(batch_size)
    events = session.execute(stmt).scalars().all()
    if not events:
        return 0

    client = OpenSearch(hosts=[settings.opensearch_url])
    actions = [
        {
            "_index": settings.opensearch_index_precedent,
            "_id": event.payload_json.get("id"),
            "_source": event.payload_json,
        }
        for event in events
        if event.type == "precedent_upserted"
    ]
    if actions:
        helpers.bulk(client, actions)

    from datetime import datetime

    for event in events:
        event.published_at = datetime.now(UTC)
    session.flush()
    return len(events)
