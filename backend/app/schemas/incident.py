import uuid
from datetime import datetime

from app.models.enums import IncidentStatus, Severity
from app.schemas.alert import AlertRead
from app.schemas.common import ORMModel
from app.schemas.investigation import InvestigationDetail
from app.schemas.remediation import RemediationActionRead
from app.schemas.verification import VerificationRead


class IncidentRead(ORMModel):
    id: uuid.UUID
    service_id: uuid.UUID
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    triggering_deployment_id: uuid.UUID | None
    detected_at: datetime
    resolved_at: datetime | None


class IncidentDetail(IncidentRead):
    alerts: list[AlertRead]
    investigations: list[InvestigationDetail]
    remediation_actions: list[RemediationActionRead]
    verifications: list[VerificationRead]
    has_postmortem: bool


class TimelineEvent(ORMModel):
    timestamp: datetime
    event_type: str
    title: str
    description: str
    metadata: dict = {}
