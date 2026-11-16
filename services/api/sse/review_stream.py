# Turns new finding rows into Server-Sent Events as a review runs, by polling the findings table.
from __future__ import annotations

import asyncio
import json
import uuid

from clausebook_core.models.review import Finding, Review
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

POLL_INTERVAL_SECONDS = 1.0


# Streams finding_ready, progress, done and error events for a running review.
def stream_review_events(db: Session, review_id: uuid.UUID) -> StreamingResponse:
    async def event_source():
        seen_finding_ids: set[uuid.UUID] = set()
        while True:
            db.expire_all()
            review = db.get(Review, review_id)
            if review is None:
                yield _sse_event("error", {"message": "Review not found"})
                return

            findings = db.query(Finding).filter(Finding.review_id == review_id).all()
            for finding in findings:
                if finding.id not in seen_finding_ids:
                    seen_finding_ids.add(finding.id)
                    yield _sse_event("finding_ready", {"finding_id": str(finding.id)})

            yield _sse_event("progress", {"findings_so_far": len(seen_finding_ids)})

            if review.status in ("done", "error"):
                yield _sse_event(review.status, {"review_id": str(review_id)})
                return

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    return StreamingResponse(event_source(), media_type="text/event-stream")


# Formats one event as an SSE wire message.
def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
