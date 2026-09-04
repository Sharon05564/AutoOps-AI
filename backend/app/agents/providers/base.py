from abc import ABC, abstractmethod
from typing import Any

from app.agents.schemas import Diagnosis, PostmortemNarrative
from app.tools.executor import ToolExecutor


class InvestigationProvider(ABC):
    """A pluggable "brain" for the investigation agent and postmortem writer.

    Every provider gets the same read-only ToolExecutor for investigation and
    is responsible for deciding which tools to call and how to reason over
    their results - it never sees or touches mutating tools
    (rollback/restart/scale). Postmortem generation reuses the same provider
    but only synthesizes prose from data the caller already gathered - it
    makes no additional tool calls.
    """

    name: str

    @abstractmethod
    async def investigate(self, executor: ToolExecutor) -> Diagnosis: ...

    @abstractmethod
    async def generate_postmortem_narrative(
        self, context: dict[str, Any]
    ) -> PostmortemNarrative: ...
