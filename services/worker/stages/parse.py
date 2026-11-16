# Stage 1: reads the uploaded document's bytes from local blob storage and extracts plain text.
from __future__ import annotations

from pathlib import Path

from clausebook_core.models.document import Document
from clausebook_core.storage.local_blob_store import find_blob

from services.worker.context import ReviewContext, StageResult
from services.worker.stage import Stage


# Extracts text from a .docx, .pdf, or plain-text file, dispatched on its extension.
def extract_text(path: Path) -> str:
    if path.suffix == ".docx":
        return _extract_docx(path)
    if path.suffix == ".pdf":
        return _extract_pdf(path)
    return path.read_text(errors="replace")


# Joins every paragraph's text, since segment_text splits on sentence and heading boundaries anyway.
def _extract_docx(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


# Joins every page's extracted text with a blank line between pages.
def _extract_pdf(path: Path) -> str:
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        return "\n\n".join(page.extract_text() or "" for page in pdf.pages)


# Reads the uploaded document's blob and extracts its text.
class ParseStage(Stage):
    name = "parse"

    def run(self, ctx: ReviewContext) -> StageResult:
        document = ctx.session.get(Document, ctx.document_id)
        if document is None:
            return StageResult(ok=False, message="Document not found")

        blob_path = find_blob(document.sha256)
        if blob_path is None:
            return StageResult(ok=False, message=f"No stored blob found for sha256={document.sha256}")

        ctx.document_text = extract_text(blob_path)
        return StageResult(ok=True, message=f"{len(ctx.document_text)} characters")
