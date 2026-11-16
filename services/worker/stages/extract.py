# Stage 4: deterministic term extraction per clause type. A missing attribute just stays absent.
from __future__ import annotations

from clausebook_core.models.firm import ClauseType

from ml.extract.extractors import extract
from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


# Runs rule-based extraction on every classified segment.
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
                # TODO(ml): run the schema-validated LLM extractor only on attributes `attrs` left empty.
        return StageResult(ok=True, message=f"{len(ctx.findings)} candidate findings")
