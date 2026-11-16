# Proves the precedent index can be rebuilt from Postgres alone: delete it, replay the outbox, compare counts.
#
# This is the test for the claim ADR 2 makes: OpenSearch holds nothing
# Postgres doesn't already have. Needs CLAUSEBOOK_DATABASE_URL and
# CLAUSEBOOK_OPENSEARCH_URL pointing at a live, seeded stack.
from __future__ import annotations

import pytest
from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.playbook import Precedent

from services.worker.outbox import relay_pending_events

pytestmark = pytest.mark.opensearch


def test_rebuilt_index_matches_precedent_count():
    from opensearchpy import OpenSearch

    settings = get_settings()
    factory = build_session_factory(settings)
    client = OpenSearch(hosts=[settings.opensearch_url])

    with session_scope(factory) as session:
        precedent_count = session.query(Precedent).count()
        assert precedent_count > 0, "seed pipelines/seed/cuad_precedent.py before running this test"

        # Mark every outbox event unpublished so the relay has everything to replay,
        # the same situation a rebuilt-from-scratch index would be in.
        from sqlalchemy import text

        session.execute(text("UPDATE outbox_event SET published_at = NULL"))
        session.flush()

    if client.indices.exists(index=settings.opensearch_index_precedent):
        client.indices.delete(index=settings.opensearch_index_precedent)

    with session_scope(factory) as session:
        relayed = 0
        while True:
            batch = relay_pending_events(session, settings, batch_size=500)
            relayed += batch
            if batch == 0:
                break

    client.indices.refresh(index=settings.opensearch_index_precedent)
    count_response = client.count(index=settings.opensearch_index_precedent)
    indexed_count = count_response["count"]

    assert indexed_count == precedent_count, (
        f"rebuilt index has {indexed_count} documents, Postgres has {precedent_count} precedent rows"
    )
