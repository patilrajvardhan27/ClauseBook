"""Scores the placement engine against the 150 hand-labeled gold clauses.

Each gold row carries the clause text, its clause type, the deal context it
was reviewed under, and the position a lawyer actually assigned it to.
Running the same text through extraction and the placement engine and
comparing the result is the single strongest evaluation in the project,
because it is the exact path a real review takes.
"""
from __future__ import annotations

from dataclasses import dataclass

from clausebook_core.placement.engine import place
from clausebook_core.placement.types import AttributeSpec, PositionSpec
from ml.extract.extractors import extract


@dataclass(frozen=True)
class GoldClause:
    clause_id: str
    clause_type_cuad_category: str
    text: str
    deal_context: dict
    gold_matched_position_id: str


@dataclass
class PlacementEvalReport:
    total: int
    matched_correct: int
    confusion: dict[str, dict[str, int]]  # gold rank label -> predicted rank label -> count

    @property
    def matched_position_accuracy(self) -> float:
        return self.matched_correct / self.total if self.total else 0.0


def evaluate_placement(
    gold: list[GoldClause],
    ladder_by_category: dict[str, list[PositionSpec]],
    attribute_specs_by_category: dict[str, dict[str, AttributeSpec]],
) -> PlacementEvalReport:
    correct = 0
    confusion: dict[str, dict[str, int]] = {}

    for clause in gold:
        attrs = extract(clause.clause_type_cuad_category, clause.text)
        ladder = ladder_by_category.get(clause.clause_type_cuad_category, [])
        attribute_specs = attribute_specs_by_category.get(clause.clause_type_cuad_category, {})

        result = place(attrs, ladder, clause.deal_context, attribute_specs)
        predicted = result.matched_position_id or "outside_playbook"
        gold_label = clause.gold_matched_position_id

        confusion.setdefault(gold_label, {}).setdefault(predicted, 0)
        confusion[gold_label][predicted] += 1

        if predicted == gold_label:
            correct += 1

    return PlacementEvalReport(total=len(gold), matched_correct=correct, confusion=confusion)
