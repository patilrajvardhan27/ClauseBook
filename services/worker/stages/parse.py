# Stage 1: pulls raw text for the document, cached by its SHA-256.
from __future__ import annotations

from clausebook_core.models.document import Document

from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


# Reads cached document text; a real parser (python-docx, pdfplumber) plugs in here.
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
