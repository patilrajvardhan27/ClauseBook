"""Splits a contract's raw text into clause-sized segments.

Numbered and lettered sections first, because that is how most commercial
contracts are actually structured; a sentence-boundary fallback handles the
minority with no numbering at all. Neither pass is a model -- segmentation
runs before classification and has to work with zero training data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_SECTION_HEADING = re.compile(
    r"^\s*(?:(?:Section\s+)?\d+(?:\.\d+)*\.?|\([a-z]\)|[A-Z]\.)\s+(.{0,80})$",
    re.MULTILINE,
)
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.;])\s+(?=[A-Z])")

MIN_SEGMENT_CHARS = 40  # shorter spans are almost always headings or stray numbering, not clauses


@dataclass(frozen=True)
class RawSegment:
    ord: int
    start_char: int
    end_char: int
    text: str
    heading: str | None


def segment_text(document_text: str) -> list[RawSegment]:
    headings = list(_SECTION_HEADING.finditer(document_text))
    if len(headings) >= 3:
        return _segment_by_headings(document_text, headings)
    return _segment_by_sentences(document_text)


def _segment_by_headings(text: str, headings: list[re.Match]) -> list[RawSegment]:
    segments: list[RawSegment] = []
    bounds = [h.start() for h in headings] + [len(text)]
    for i, heading_match in enumerate(headings):
        start, end = bounds[i], bounds[i + 1]
        body = text[start:end].strip()
        if len(body) < MIN_SEGMENT_CHARS:
            continue
        segments.append(
            RawSegment(ord=len(segments), start_char=start, end_char=end, text=body, heading=heading_match.group(1).strip())
        )
    return segments


def _segment_by_sentences(text: str) -> list[RawSegment]:
    segments: list[RawSegment] = []
    cursor = 0
    for chunk in _SENTENCE_BOUNDARY.split(text):
        chunk = chunk.strip()
        start = text.find(chunk, cursor)
        if start == -1 or len(chunk) < MIN_SEGMENT_CHARS:
            cursor = max(cursor, start + len(chunk)) if start != -1 else cursor
            continue
        end = start + len(chunk)
        segments.append(RawSegment(ord=len(segments), start_char=start, end_char=end, text=chunk, heading=None))
        cursor = end
    return segments
