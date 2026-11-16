# Relays outbox rows into OpenSearch; Postgres stays the source of truth (see ADR 2).
from __future__ import annotations

from datetime import UTC, datetime

from clausebook_core.config.settings import Settings
from clausebook_core.models.job import OutboxEvent
from sqlalchemy import select
from sqlalchemy.orm import Session

EMBEDDING_DIMENSIONS = 384  # bge-small-en-v1.5's output size; change together if the model changes


# Creates the precedent index with a knn-enabled mapping if it doesn't exist yet.
def _ensure_index(client, index_name: str) -> None:
    if client.indices.exists(index=index_name):
        return
    client.indices.create(
        index=index_name,
        body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "clause_text": {"type": "text"},
                    "clause_type": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": EMBEDDING_DIMENSIONS,
                        "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"},
                    },
                }
            },
        },
    )


# Indexes every unpublished outbox event into OpenSearch, computing each one's embedding, and marks it published.
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
    _ensure_index(client, settings.opensearch_index_precedent)

    upsert_events = [e for e in events if e.type == "precedent_upserted"]
    if upsert_events:
        from ml.retrieve.embeddings import embed_batch

        texts = [e.payload_json.get("clause_text", "") for e in upsert_events]
        vectors = embed_batch(settings, texts)

        actions = [
            {
                "_index": settings.opensearch_index_precedent,
                "_id": event.payload_json.get("id"),
                "_source": {**event.payload_json, "embedding": vector},
            }
            for event, vector in zip(upsert_events, vectors)
        ]
        helpers.bulk(client, actions)

    for event in events:
        event.published_at = datetime.now(UTC)
    session.flush()
    return len(events)
