import uuid
from datetime import datetime
from typing import Any

from app.models.enums import ActionType, RemediationStatus, RiskLevel
from app.schemas.approval import ApprovalRead
from app.schemas.common import ORMModel


class RemediationActionRead(ORMModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    action_type: ActionType
    risk_level: RiskLevel
    status: RemediationStatus
    parameters: dict[str, Any]
    result: dict[str, Any]
    idempotency_key: str
    attempt_number: int
    created_at: datetime
    executed_at: datetime | None
    approval: ApprovalRead | None = None
