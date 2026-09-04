import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class AlertRead(ORMModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    service_id: uuid.UUID
    metric_name: str
    value: float
    threshold: float
    message: str
    triggered_at: datetime
