# Stage 6: runs the same placement engine the API's preview endpoint uses, on each candidate finding.
from __future__ import annotations

from clausebook_core.placement.engine import place

from services.api.domain.playbook_loader import load_attribute_specs, load_ladder
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


# Ladders and places every finding, holding off on positions already rejected.
class PlaceStage(Stage):
    name = "place"

    def run(self, ctx: ReviewContext) -> StageResult:
        for finding in ctx.findings:
            clause_type_id = finding["clause_type"].id
            ladder = load_ladder(ctx.session, ctx.playbook_id, clause_type_id)
            attribute_specs = load_attribute_specs(ctx.session, clause_type_id)
            rejected = self._rejected_positions(ctx, clause_type_id)

            result = place(finding["attrs"], ladder, ctx.deal_context, attribute_specs, rejected)
            finding["placement"] = result
        return StageResult(ok=True)

    # Finds positions this counterparty has already rejected for this clause type.
    def _rejected_positions(self, ctx: ReviewContext, clause_type_id) -> set[str]:
        from clausebook_core.models.review import Finding

        rows = (
            ctx.session.query(Finding)
            .filter(Finding.clause_type_id == clause_type_id, Finding.decision == "rejected")
            .all()
        )
        return {str(r.proposed_position_id) for r in rows if r.proposed_position_id}
