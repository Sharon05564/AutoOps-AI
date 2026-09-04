import uuid
from datetime import datetime

from app.models.enums import InvestigationStatus
from app.schemas.agent_tool_call import AgentToolCallRead
from app.schemas.common import ORMModel


class InvestigationRead(ORMModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    status: InvestigationStatus
    llm_provider: str
    root_cause: str
    confidence: float
    summary: str
    recommended_action: str
    started_at: datetime
    completed_at: datetime | None


class InvestigationDetail(InvestigationRead):
    tool_calls: list[AgentToolCallRead]
