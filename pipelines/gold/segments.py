# Builds the gold layer: segments carrying every CUAD category that overlaps them by 50% or more.
from __future__ import annotations

from dataclasses import dataclass

from clausebook_core.segment import RawSegment, segment_text

from pipelines.silver.cuad import CuadSpan

OVERLAP_THRESHOLD = 0.5


# A segment paired with the CUAD categories whose labeled spans overlap it.
@dataclass(frozen=True)
class GoldSegment:
    contract_id: str
    segment: RawSegment
    categories: list[str]


# Segments a contract and labels each segment with its overlapping categories.
def build_gold_segments(contract_id: str, contract_text: str, spans: list[CuadSpan]) -> list[GoldSegment]:
    segments = segment_text(contract_text)
    gold: list[GoldSegment] = []

    for segment in segments:
        categories = [
            span.category
            for span in spans
            if span.contract_id == contract_id and _overlap_fraction(segment, span, contract_text) >= OVERLAP_THRESHOLD
        ]
        gold.append(GoldSegment(contract_id=contract_id, segment=segment, categories=sorted(set(categories))))

    return gold


# Fraction of a span's length that falls inside a given segment.
def _overlap_fraction(segment: RawSegment, span: CuadSpan, contract_text: str) -> float:
    span_start = span.span_start
    span_end = span_start + len(span.span_text)
    if span_start < 0:
        return 0.0

    overlap_start = max(segment.start_char, span_start)
    overlap_end = min(segment.end_char, span_end)
    overlap = max(0, overlap_end - overlap_start)

    span_len = max(span_end - span_start, 1)
    return overlap / span_len
