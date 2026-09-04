from datetime import datetime

from pydantic import BaseModel


class DeploymentInfo(BaseModel):
    id: str
    version: str
    status: str
    is_bad_deployment: bool
    deployed_at: datetime
    rolled_back_at: datetime | None = None


class MetricPoint(BaseModel):
    timestamp: datetime
    request_count: int
    error_count: int
    error_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float


class LogLine(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str = "app"


class ServiceState(BaseModel):
    service_name: str
    replicas: int
    active_deployment: DeploymentInfo
    is_degraded: bool
    latest_metrics: MetricPoint | None


class ScaleRequest(BaseModel):
    replicas: int
