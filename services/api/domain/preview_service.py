# Backs POST /v1/playbooks/{id}/preview: places one pasted clause with no review or job queue.
from __future__ import annotations

import uuid

from clausebook_core.models.firm import ClauseType
from clausebook_core.placement.engine import place
from sqlalchemy.orm import Session

from ml.extract.extractors import extract
from services.api.domain.playbook_loader import load_attribute_specs, load_ladder


# Extracts, ladders and places a pasted clause, with no document or review behind it.
def preview_placement(
    session: Session,
    clause_text: str,
    clause_type_id: uuid.UUID,
    playbook_id: uuid.UUID,
    deal_context: dict,
) -> dict:
    clause_type = session.get(ClauseType, clause_type_id)
    cuad_category = clause_type.cuad_category if clause_type else ""

    attrs = extract(cuad_category, clause_text)
    ladder = load_ladder(session, playbook_id, clause_type_id)
    attribute_specs = load_attribute_specs(session, clause_type_id)

    result = place(attrs, ladder, deal_context, attribute_specs)
    return {
        "attrs": attrs,
        "matched_position_id": result.matched_position_id,
        "proposed_position_id": result.proposed_position_id,
        "outside_playbook": result.outside_playbook,
        "reason": result.reason,
    }
