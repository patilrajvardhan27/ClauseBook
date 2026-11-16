# Chains the review stages in order, timing and logging each one.
from __future__ import annotations

import logging
import time

from services.worker.context import ReviewContext
from services.worker.stages.classify import ClassifyStage
from services.worker.stages.extract import ExtractStage
from services.worker.stages.parse import ParseStage
from services.worker.stages.place import PlaceStage
from services.worker.stages.redline import RedlineStage
from services.worker.stages.retrieve import RetrieveStage
from services.worker.stages.segment import SegmentStage

logger = logging.getLogger("clausebook.worker")

STAGES = [ParseStage(), SegmentStage(), ClassifyStage(), ExtractStage(), RetrieveStage(), PlaceStage(), RedlineStage()]


# Runs every stage in order on one review, stopping at the first failure.
def run_review_pipeline(ctx: ReviewContext) -> None:
    for stage in STAGES:
        started = time.monotonic()
        result = stage.run(ctx)
        elapsed_ms = (time.monotonic() - started) * 1000
        logger.info("stage=%s ok=%s elapsed_ms=%.1f %s", stage.name, result.ok, elapsed_ms, result.message)
        if not result.ok:
            raise RuntimeError(f"Stage {stage.name} failed: {result.message}")
