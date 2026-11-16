# A Postgres job queue using FOR UPDATE SKIP LOCKED, chosen over a broker (see ADR 1).
from __future__ import annotations

from datetime import UTC, datetime

from clausebook_core.models.job import Job
from sqlalchemy import select
from sqlalchemy.orm import Session

MAX_ATTEMPTS = 3


# Claims and locks the next pending job of a given kind.
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


# Marks a job done.
def complete_job(session: Session, job: Job) -> None:
    job.status = "done"
    session.flush()


# Requeues a job if it has attempts left, else marks it permanently failed.
def fail_job(session: Session, job: Job, error: str) -> None:
    job.status = "pending" if job.attempts < MAX_ATTEMPTS else "failed"
    session.flush()
