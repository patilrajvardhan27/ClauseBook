"""Worker loop entrypoint: claim a job, run the review pipeline, mark it done.

Runs as its own process (see deploy/docker-compose.yml) separate from the
API, so a slow review never blocks a request thread.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

from clausebook_core.config.settings import get_settings
from clausebook_core.db.session import build_session_factory, session_scope
from clausebook_core.models.review import Review

from services.worker.context import ReviewContext
from services.worker.outbox import relay_pending_events
from services.worker.pipeline import run_review_pipeline
from services.worker.queue import claim_next_job, complete_job, fail_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clausebook.worker")

POLL_SECONDS = 1.0


def main() -> None:
    settings = get_settings()
    factory = build_session_factory(settings)

    while True:
        processed = False
        with session_scope(factory) as session:
            job = claim_next_job(session, kind="run_review")
            if job is not None:
                processed = True
                _run_review_job(session, job)
            relay_pending_events(session, settings)

        if not processed:
            time.sleep(POLL_SECONDS)


def _run_review_job(session, job) -> None:
    review_id = uuid.UUID(job.payload_json["review_id"])
    review = session.get(Review, review_id)
    review.status = "running"
    review.started_at = datetime.now(UTC)
    session.flush()

    try:
        ctx = ReviewContext(
            review_id=review.id,
            document_id=review.document_id,
            playbook_id=review.playbook_id,
            deal_context=job.payload_json.get("deal_context", {}),
            session=session,
        )
        run_review_pipeline(ctx)
        review.status = "done"
        complete_job(session, job)
    except Exception as exc:
        logger.exception("review %s failed", review_id)
        review.status = "error"
        fail_job(session, job, str(exc))
    finally:
        review.finished_at = datetime.now(UTC)
        session.flush()


if __name__ == "__main__":
    main()
