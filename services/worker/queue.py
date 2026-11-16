"""A Postgres job queue using FOR UPDATE SKIP LOCKED.

Chosen over a broker (ADR 1) so a job's state commits in the same
transaction as the review it drives: there is no window where a job exists
but the review row does not, or vice versa. Revisit only past roughly 50
jobs per second, which a single-firm deployment will not reach.
"""
from __future__ import annotations

from datetime import UTC, datetime

from clausebook_core.models.job import Job
from sqlalchemy import select
from sqlalchemy.orm import Session

MAX_ATTEMPTS = 3


def claim_next_job(session: Session, kind: str) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.kind == kind, Job.status == "pending", Job.run_after <= datetime.now(UTC))
        .order_by(Job.run_after)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = session.execute(stmt).scalar_one_or_none()
    if job is not None:
        job.status = "running"
        job.locked_at = datetime.now(UTC)
        job.attempts += 1
        session.flush()
    return job


def complete_job(session: Session, job: Job) -> None:
    job.status = "done"
    session.flush()


def fail_job(session: Session, job: Job, error: str) -> None:
    job.status = "pending" if job.attempts < MAX_ATTEMPTS else "failed"
    session.flush()
