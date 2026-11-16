# Shared state passed between worker stages for a single review run.
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session


# State one review run carries through every stage.
@dataclass
class ReviewContext:
    review_id: uuid.UUID
    document_id: uuid.UUID
    playbook_id: uuid.UUID
    deal_context: dict
    session: Session
    document_text: str = ""
    segments: list = field(default_factory=list)
    findings: list = field(default_factory=list)


# Whether a stage succeeded, and a short message for the logs.
@dataclass
class StageResult:
    ok: bool
    message: str = ""
