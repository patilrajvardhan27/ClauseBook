"""Stage 2: splits document text into clause-sized segments and persists them."""
from __future__ import annotations

from clausebook_core.models.document import Segment
from clausebook_core.segment import segment_text
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


class SegmentStage(Stage):
    name = "segment"

    def run(self, ctx: ReviewContext) -> StageResult:
        raw_segments = segment_text(ctx.document_text)
        for raw in raw_segments:
            row = Segment(
                document_id=ctx.document_id,
                ord=raw.ord,
                start_char=raw.start_char,
                end_char=raw.end_char,
                text=raw.text,
                heading=raw.heading,
            )
            ctx.session.add(row)
            ctx.segments.append(row)
        ctx.session.flush()
        return StageResult(ok=True, message=f"{len(ctx.segments)} segments")
