import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class ServiceRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    replicas: int
    active_deployment_id: uuid.UUID | None
    last_seen_at: datetime | None
    created_at: datetime


class ServiceHealth(ORMModel):
    service: ServiceRead
    error_rate: float
    latency_p95_ms: float
    active_incidents: int
    status: str
