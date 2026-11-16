"""Stage 5: attaches retrieved precedent to each candidate finding as
supporting evidence, not as the basis for the placement decision itself
(see place.py and the ranking note in clausebook_core.placement.engine)."""
from __future__ import annotations

from clausebook_core.config.settings import get_settings

from ml.retrieve.hybrid import hybrid_search
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


class RetrieveStage(Stage):
    name = "retrieve"

    def run(self, ctx: ReviewContext) -> StageResult:
        settings = get_settings()
        for finding in ctx.findings:
            hits = hybrid_search(
                settings, query=finding["segment"].text, clause_type=finding["clause_type"].name, top_k=5
            )
            finding["precedent_hits"] = hits
        return StageResult(ok=True)
