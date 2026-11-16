"""Percentiles of deal terms across the precedent corpus.

Backs the analytics page's "what counts as standard" view. Kept as a plain
function over a list of numbers so a pandas recomputation in a test can
check it against the exact same inputs with no database involved.
"""
from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

PERCENTILES = (10, 25, 50, 75, 90)


def percentiles_for_values(values: list[float]) -> dict[int, float]:
    if not values:
        return {p: 0.0 for p in PERCENTILES}
    return {p: float(np.percentile(values, p)) for p in PERCENTILES}


def clause_type_percentiles(session: Session, clause_type_name: str) -> dict:
    from clausebook_core.models.firm import ClauseType
    from clausebook_core.models.playbook import Precedent

    clause_type = session.query(ClauseType).filter(ClauseType.name == clause_type_name).one_or_none()
    if clause_type is None:
        return {"clause_type": clause_type_name, "attributes": {}}

    precedents = session.query(Precedent).filter(Precedent.clause_type_id == clause_type.id).all()

    by_attribute: dict[str, list[float]] = {}
    for precedent in precedents:
        for key, value in precedent.attrs_json.items():
            if isinstance(value, (int, float)):
                by_attribute.setdefault(key, []).append(float(value))

    return {
        "clause_type": clause_type_name,
        "attributes": {key: percentiles_for_values(values) for key, values in by_attribute.items()},
    }
