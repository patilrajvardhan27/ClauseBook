"""Normalizes CUAD's SQuAD-style JSON into one row per (contract, category,
labeled span). This is the layer every downstream consumer reads -- the
classifier's training set, the precedent corpus and the gold-label tool all
read silver, never bronze's raw JSON.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuadSpan:
    contract_id: str
    contract_title: str
    category: str
    span_text: str
    span_start: int


def normalize(cuad_json: dict) -> list[CuadSpan]:
    spans: list[CuadSpan] = []
    for entry in cuad_json.get("data", []):
        contract_title = entry.get("title", "")
        for paragraph in entry.get("paragraphs", []):
            for qa in paragraph.get("qas", []):
                category = _category_from_question(qa.get("question", ""))
                for answer in qa.get("answers", []):
                    spans.append(
                        CuadSpan(
                            contract_id=contract_title,
                            contract_title=contract_title,
                            category=category,
                            span_text=answer.get("text", ""),
                            span_start=answer.get("answer_start", -1),
                        )
                    )
    return spans


def _category_from_question(question: str) -> str:
    """CUAD encodes the category inside its question template, e.g.
    'Highlight the parts ... related to "Cap On Liability"'. Extracted once
    here so every downstream consumer agrees on the category string."""
    if '"' not in question:
        return question.strip()
    parts = question.split('"')
    return parts[1] if len(parts) >= 2 else question.strip()
