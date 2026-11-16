# Turns two clause strings into the smallest set of insert/delete hunks.
from __future__ import annotations

from dataclasses import dataclass

from diff_match_patch import diff_match_patch

_DMP = diff_match_patch()


# One run of equal, inserted or deleted text in a word-level diff.
@dataclass(frozen=True)
class Hunk:
    op: str  # "equal" | "insert" | "delete"
    text: str


# Diffs two strings and merges adjacent same-operation runs into word-level hunks.
def word_diff(source_text: str, target_text: str) -> list[Hunk]:
    diffs = _DMP.diff_main(source_text, target_text)
    _DMP.diff_cleanupSemantic(diffs)

    op_names = {0: "equal", 1: "insert", -1: "delete"}
    return [Hunk(op=op_names[op], text=text) for op, text in diffs if text]


# Fraction of the source text's length the diff actually touches.
def edit_distance_ratio(source_text: str, target_text: str) -> float:
    if not source_text:
        return 1.0 if target_text else 0.0
    hunks = word_diff(source_text, target_text)
    changed_chars = sum(len(h.text) for h in hunks if h.op != "equal")
    return changed_chars / max(len(source_text), 1)
