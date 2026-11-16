"""Stage 7: builds the minimal tracked-change diff and persists the finding.

The LLM only adapts approved language to the extracted terms (e.g. swapping
in the counterparty's own notice period into otherwise-approved wording);
it never drafts freely, and its output here is plain string substitution
until services/worker/wording.py's schema-validated LLM call is wired in.
"""
from __future__ import annotations

from clausebook_core.diff.minimal_diff import edit_distance_ratio, word_diff
from clausebook_core.models.review import Finding
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


class RedlineStage(Stage):
    name = "redline"

    def run(self, ctx: ReviewContext) -> StageResult:
        for item in ctx.findings:
            placement = item["placement"]
            target_text = self._approved_text_for(ctx, placement.proposed_position_id)
            source_text = item["segment"].text

            hunks = word_diff(source_text, target_text) if target_text else []
            row = Finding(
                review_id=ctx.review_id,
                segment_id=item["segment"].id,
                clause_type_id=item["clause_type"].id,
                confidence=0.0,  # set by classify.py once the real classifier reports a probability
                attrs_json=item["attrs"],
                matched_position_id=_uuid_or_none(placement.matched_position_id),
                proposed_position_id=_uuid_or_none(placement.proposed_position_id),
                redline_json={
                    "hunks": [{"op": h.op, "text": h.text} for h in hunks],
                    "edit_ratio": edit_distance_ratio(source_text, target_text) if target_text else 0.0,
                },
                evidence_json={
                    "precedent_hits": item.get("precedent_hits", []),
                    "reason": placement.reason,
                    "better_attributes": placement.better_attributes,
                },
            )
            ctx.session.add(row)
        ctx.session.flush()
        return StageResult(ok=True)

    def _approved_text_for(self, ctx: ReviewContext, position_id: str | None) -> str | None:
        if position_id is None:
            return None
        from clausebook_core.models.playbook import ApprovedLanguage

        row = (
            ctx.session.query(ApprovedLanguage)
            .filter(ApprovedLanguage.position_id == _uuid_or_none(position_id))
            .first()
        )
        return row.text if row else None


def _uuid_or_none(value):
    import uuid

    return uuid.UUID(value) if value else None
