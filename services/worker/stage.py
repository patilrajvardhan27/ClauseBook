"""The one interface every worker stage implements.

Timing, retries and tracing wrap this interface once in queue.py, rather
than being copy-pasted into each stage. A new stage is just a new subclass;
nothing else in the worker needs to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from services.worker.context import ReviewContext, StageResult


class Stage(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: ReviewContext) -> StageResult:
        ...
