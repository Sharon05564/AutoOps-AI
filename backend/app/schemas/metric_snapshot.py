import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class MetricSnapshotRead(ORMModel):
    id: uuid.UUID
    service_id: uuid.UUID
    timestamp: datetime
    request_count: int
    error_count: int
    error_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
