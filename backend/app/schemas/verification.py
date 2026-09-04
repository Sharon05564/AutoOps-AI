import uuid
from datetime import datetime
from typing import Any

from app.models.enums import VerificationStatus
from app.schemas.common import ORMModel


class VerificationRead(ORMModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    remediation_action_id: uuid.UUID
    status: VerificationStatus
    metrics_before: dict[str, Any]
    metrics_after: dict[str, Any]
    checked_at: datetime
