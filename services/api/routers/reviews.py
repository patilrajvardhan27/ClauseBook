# Starts a review and streams its findings as they finish.
from __future__ import annotations

import uuid

from clausebook_core.models.job import Job
from clausebook_core.models.review import Review
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.api.deps import get_db
from services.api.schemas import ReviewCreate, ReviewOut
from services.api.sse.review_stream import stream_review_events

router = APIRouter()


# Queues a review by writing the review row and its job in one transaction.
@router.post("", status_code=202, response_model=ReviewOut)
def start_review(payload: ReviewCreate, db: Session = Depends(get_db)) -> Review:
    review = Review(
        document_id=payload.document_id,
        playbook_id=payload.playbook_id,
        playbook_version=1,
        status="queued",
    )
    db.add(review)
    db.flush()

    db.add(
        Job(
            kind="run_review",
            payload_json={"review_id": str(review.id), "deal_context": payload.deal_context.model_dump()},
        )
    )
    return review


# SSE stream of segment_found, finding_ready, progress, done and error events.
@router.get("/{review_id}/events")
def review_events(review_id: uuid.UUID, db: Session = Depends(get_db)):
    return stream_review_events(db, review_id)


# Fetches one review's current status.
@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: uuid.UUID, db: Session = Depends(get_db)) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
