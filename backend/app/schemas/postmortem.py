import uuid
from datetime import datetime
from typing import Any

from app.schemas.common import ORMModel


class PostmortemRead(ORMModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    summary: str
    root_cause: str
    timeline: list[dict[str, Any]]
    evidence: list[str]
    remediation_summary: str
    recovery_verification: str
    prevention_recommendations: list[str]
    markdown_report: str
    generated_at: datetime
