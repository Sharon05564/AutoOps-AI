import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_tool_call import AgentToolCall
from app.tools import read_only

_TOOL_FUNCTIONS = {
    "get_service_health": read_only.get_service_health,
    "get_recent_metrics": read_only.get_recent_metrics,
    "get_recent_logs": read_only.get_recent_logs,
    "get_recent_deployments": read_only.get_recent_deployments,
    "get_incident_context": read_only.get_incident_context,
}


class ToolExecutor:
    """Executes read-only tools on behalf of the investigation agent.

    Binds the service/incident being investigated so the agent only needs to
    supply the tool's own arguments, and records every call as an
    AgentToolCall row for the audit trail.
    """

    def __init__(
        self,
        session: AsyncSession,
        investigation_id: uuid.UUID,
        service_id: uuid.UUID,
        incident_id: uuid.UUID,
    ):
        self.session = session
        self.investigation_id = investigation_id
        self.service_id = service_id
        self.incident_id = incident_id

    async def execute(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        arguments = arguments or {}
        func = _TOOL_FUNCTIONS.get(tool_name)
        if func is None:
            return {"error": f"unknown tool: {tool_name}"}

        call_kwargs = dict(arguments)
        if tool_name == "get_incident_context":
            call_kwargs.setdefault("incident_id", self.incident_id)
        else:
            call_kwargs.setdefault("service_id", self.service_id)

        started = time.perf_counter()
        result = await func(self.session, **call_kwargs)
        duration_ms = (time.perf_counter() - started) * 1000

        self.session.add(
            AgentToolCall(
                investigation_id=self.investigation_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result if isinstance(result, dict) else {"items": result},
                duration_ms=duration_ms,
            )
        )
        await self.session.flush()
        return result
