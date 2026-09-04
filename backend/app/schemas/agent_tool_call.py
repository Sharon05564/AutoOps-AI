import uuid
from datetime import datetime
from typing import Any

from app.schemas.common import ORMModel


class AgentToolCallRead(ORMModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    duration_ms: float
    called_at: datetime
