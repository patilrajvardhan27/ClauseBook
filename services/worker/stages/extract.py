"""Stage 4: deterministic term extraction per clause type.

Rules run first (ml/extract). The plan reserves a schema-validated LLM
fallback for attributes rules miss; it is not wired into this slice -- see
the TODO below -- so an unmatched attribute just stays absent, which the
placement engine already treats as "condition cannot be satisfied".
"""
from __future__ import annotations

from clausebook_core.models.firm import ClauseType

from ml.extract.extractors import extract
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


class ExtractStage(Stage):
    name = "extract"

    def run(self, ctx: ReviewContext) -> StageResult:
        clause_type_by_name = {
            ct.name: ct for ct in ctx.session.query(ClauseType).all()
        }
        for segment in ctx.segments:
            labels = getattr(segment, "predicted_labels", [])
            for label in labels:
                clause_type = clause_type_by_name.get(label)
                if clause_type is None:
                    continue
                attrs = extract(clause_type.cuad_category, segment.text)
                ctx.findings.append(
                    {"segment": segment, "clause_type": clause_type, "attrs": attrs, "label": label}
                )
                # TODO(ml): run the LLM extractor (Pydantic-validated) only on
                # attributes `attrs` left empty, per section 5's extraction row.
        return StageResult(ok=True, message=f"{len(ctx.findings)} candidate findings")
