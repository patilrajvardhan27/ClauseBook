# Normalizes CUAD's SQuAD-style JSON into one row per contract/category/labeled span.
from __future__ import annotations

from dataclasses import dataclass


# One labeled span: which contract, which category, and where it sits.
@dataclass(frozen=True)
class CuadSpan:
    contract_id: str
    contract_title: str
    category: str
    span_text: str
    span_start: int


# Flattens CUAD's nested JSON into a list of labeled spans.
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


# Pulls the quoted category name out of CUAD's question template.
def _category_from_question(question: str) -> str:
    if '"' not in question:
        return question.strip()
    parts = question.split('"')
    return parts[1] if len(parts) >= 2 else question.strip()
