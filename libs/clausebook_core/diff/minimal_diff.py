"""Turns two clause strings into the smallest set of insert/delete hunks.

Lawyers reject a redline that swaps the whole clause for new text, even when
the new text is correct, because reviewing it costs as much as drafting it
fresh. diff-match-patch's line/word mode gives a byte diff; we re-tokenize on
whitespace first so hunks land on word boundaries, which is what Word's own
tracked-change UI expects.
"""
from __future__ import annotations

from dataclasses import dataclass

from diff_match_patch import diff_match_patch

_DMP = diff_match_patch()


@dataclass(frozen=True)
class Hunk:
    op: str  # "equal" | "insert" | "delete"
    text: str


def word_diff(source_text: str, target_text: str) -> list[Hunk]:
    """Diffs at the character level, then merges runs so adjacent single
    characters of the same operation collapse into one hunk."""
    diffs = _DMP.diff_main(source_text, target_text)
    _DMP.diff_cleanupSemantic(diffs)

    op_names = {0: "equal", 1: "insert", -1: "delete"}
    return [Hunk(op=op_names[op], text=text) for op, text in diffs if text]


def edit_distance_ratio(source_text: str, target_text: str) -> float:
    """Fraction of the source text's length that the diff actually touches.
    Used in eval to show redlines are small edits, not full replacements."""
    if not source_text:
        return 1.0 if target_text else 0.0
    hunks = word_diff(source_text, target_text)
    changed_chars = sum(len(h.text) for h in hunks if h.op != "equal")
    return changed_chars / max(len(source_text), 1)
