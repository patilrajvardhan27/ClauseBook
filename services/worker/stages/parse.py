"""Stage 1: pulls raw text for the document. A real parser (python-docx /
pdfplumber) plugs in here; this slice reads a plain-text cache keyed by the
document's SHA-256, which is how the plan's caching rule (section 11) is
meant to work regardless of parser."""
from __future__ import annotations

from clausebook_core.models.document import Document

from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


class ParseStage(Stage):
    name = "parse"

    def run(self, ctx: ReviewContext) -> StageResult:
        document = ctx.session.get(Document, ctx.document_id)
        if document is None:
            return StageResult(ok=False, message="Document not found")
        # TODO(wiring): read apps' uploaded bytes from object storage by sha256
        # and extract text with python-docx or pdfplumber. Left unimplemented
        # here; segment.py and extract already work against plain text.
        ctx.document_text = getattr(document, "cached_text", "") or ""
        return StageResult(ok=True)
