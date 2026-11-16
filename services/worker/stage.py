# The one interface every worker stage implements.
from __future__ import annotations

from abc import ABC, abstractmethod

from services.worker.context import ReviewContext, StageResult


# A single pipeline step; a new stage is just a new subclass.
class Stage(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: ReviewContext) -> StageResult:
        ...
