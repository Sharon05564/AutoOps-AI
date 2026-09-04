from abc import ABC, abstractmethod

from app.agents.schemas import Diagnosis
from app.tools.executor import ToolExecutor


class InvestigationProvider(ABC):
    """A pluggable "brain" for the investigation agent.

    Every provider gets the same read-only ToolExecutor and is responsible
    for deciding which tools to call and how to reason over their results -
    it never sees or touches mutating tools (rollback/restart/scale).
    """

    name: str

    @abstractmethod
    async def investigate(self, executor: ToolExecutor) -> Diagnosis: ...
