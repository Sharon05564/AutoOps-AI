import random
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.config import SimulatorSettings
from app.metrics import record_tick
from app.schemas import DeploymentInfo, LogLine, MetricPoint, ServiceState

BASELINE_ERROR_RATE = 0.01
BASELINE_LATENCY_P50_MS = 40.0
BASELINE_LATENCY_P95_MS = 90.0
BASELINE_LATENCY_P99_MS = 150.0

DEGRADED_ERROR_RATE = 0.45
DEGRADED_LATENCY_P50_MS = 350.0
DEGRADED_LATENCY_P95_MS = 950.0
DEGRADED_LATENCY_P99_MS = 1600.0

DB_ERROR_MESSAGES = [
    "sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: remaining connection "
    "slots are reserved for non-replication superuser connections",
    'psycopg2.OperationalError: connection to server at "db" (10.0.0.5), port 5432 failed: '
    "Connection timed out",
    "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection "
    "timed out, timeout 30",
    "asyncpg.exceptions.TooManyConnectionsError: too many connections for role \"app_user\"",
]

INFO_ROUTES = ["/api/checkout", "/api/cart/add", "/api/inventory", "/api/payments/authorize"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Deployment:
    id: str
    version: str
    status: str
    is_bad_deployment: bool
    deployed_at: datetime
    rolled_back_at: datetime | None = None
    rolled_back_from_id: str | None = None

    def to_schema(self) -> DeploymentInfo:
        return DeploymentInfo(
            id=self.id,
            version=self.version,
            status=self.status,
            is_bad_deployment=self.is_bad_deployment,
            deployed_at=self.deployed_at,
            rolled_back_at=self.rolled_back_at,
        )


@dataclass
class SimulatorState:
    settings: SimulatorSettings
    deployments: list[Deployment] = field(default_factory=list)
    replicas: int = 3
    metrics_history: deque = field(default_factory=deque)
    log_buffer: deque = field(default_factory=deque)

    def __post_init__(self) -> None:
        self.metrics_history = deque(maxlen=self.settings.history_ticks)
        self.log_buffer = deque(maxlen=self.settings.log_buffer_size)
        self._seed_initial_deployment()

    def _seed_initial_deployment(self) -> None:
        self.deployments = [
            Deployment(
                id=str(uuid.uuid4()),
                version="v1.0.0",
                status="ACTIVE",
                is_bad_deployment=False,
                deployed_at=_now(),
            )
        ]

    @property
    def active_deployment(self) -> Deployment:
        for deployment in reversed(self.deployments):
            if deployment.status == "ACTIVE":
                return deployment
        raise RuntimeError("no active deployment - simulator state is corrupt")

    @property
    def is_degraded(self) -> bool:
        return self.active_deployment.is_bad_deployment

    # --- mutating operations -------------------------------------------------

    def trigger_bad_deployment(self) -> Deployment:
        previous = self.active_deployment
        previous.status = "SUPERSEDED"
        version = f"v1.0.{len(self.deployments)}"
        bad_deployment = Deployment(
            id=str(uuid.uuid4()),
            version=version,
            status="ACTIVE",
            is_bad_deployment=True,
            deployed_at=_now(),
        )
        self.deployments.append(bad_deployment)
        self._log("INFO", f"Deploying {version} to {self.settings.service_name}", source="deploy")
        self._log(
            "ERROR",
            f"{version} misconfigured DB pool size (max_connections=5) - connections exhausted "
            "under normal load",
            source="deploy",
        )
        return bad_deployment

    def rollback(self) -> Deployment | None:
        active = self.active_deployment
        if not active.is_bad_deployment:
            return None

        previous = next(
            (d for d in reversed(self.deployments) if d.id != active.id and d.status == "SUPERSEDED"),
            None,
        )
        active.status = "ROLLED_BACK"
        active.rolled_back_at = _now()
        if previous is not None:
            previous.status = "ACTIVE"
            active.rolled_back_from_id = previous.id
        self._log(
            "INFO",
            f"Rolled back {active.version} -> "
            f"{previous.version if previous else 'unknown'}",
            source="deploy",
        )
        return previous

    def restart(self) -> None:
        self._log("INFO", f"Restarting {self.settings.service_name} pods", source="ops")

    def scale(self, replicas: int) -> None:
        if replicas < 1 or replicas > 20:
            raise ValueError("replicas must be between 1 and 20")
        self.replicas = replicas
        self._log(
            "INFO", f"Scaled {self.settings.service_name} to {replicas} replicas", source="ops"
        )

    def reset(self) -> None:
        self.replicas = 3
        self.metrics_history.clear()
        self.log_buffer.clear()
        self._seed_initial_deployment()
        self._log("INFO", "Simulator state reset to healthy baseline", source="ops")

    # --- tick / telemetry generation -----------------------------------------

    def tick(self) -> MetricPoint:
        degraded = self.is_degraded
        request_count = random.randint(
            self.settings.requests_per_tick_min, self.settings.requests_per_tick_max
        )

        if degraded:
            error_rate = max(0.0, min(0.95, DEGRADED_ERROR_RATE + random.uniform(-0.05, 0.05)))
            error_rate += max(0, self.replicas - 3) * 0.03
            error_rate = min(0.95, error_rate)
            p50 = DEGRADED_LATENCY_P50_MS + random.uniform(-40, 40)
            p95 = DEGRADED_LATENCY_P95_MS + random.uniform(-80, 80)
            p99 = DEGRADED_LATENCY_P99_MS + random.uniform(-150, 150)
        else:
            error_rate = max(0.0, BASELINE_ERROR_RATE + random.uniform(-0.008, 0.012))
            capacity_bonus = max(0, self.replicas - 3) * 4
            p50 = max(20.0, BASELINE_LATENCY_P50_MS - capacity_bonus + random.uniform(-8, 8))
            p95 = max(40.0, BASELINE_LATENCY_P95_MS - capacity_bonus + random.uniform(-15, 15))
            p99 = max(60.0, BASELINE_LATENCY_P99_MS - capacity_bonus + random.uniform(-25, 25))

        error_count = int(request_count * error_rate)
        latencies_ms = [max(5.0, random.gauss(p50, max(p95 - p50, 1) / 2)) for _ in range(request_count)]

        point = MetricPoint(
            timestamp=_now(),
            request_count=request_count,
            error_count=error_count,
            error_rate=round(error_count / request_count, 4) if request_count else 0.0,
            latency_p50_ms=round(p50, 2),
            latency_p95_ms=round(p95, 2),
            latency_p99_ms=round(p99, 2),
        )
        self.metrics_history.append(point)
        record_tick(self.settings.service_name, request_count, error_count, latencies_ms)
        self._generate_logs(request_count, error_count, p50)
        return point

    def _generate_logs(self, request_count: int, error_count: int, p50: float) -> None:
        for _ in range(min(error_count, 8)):
            self._log("ERROR", random.choice(DB_ERROR_MESSAGES), source="app")
        for _ in range(min(request_count - error_count, 12)):
            route = random.choice(INFO_ROUTES)
            latency = max(5.0, random.gauss(p50, 15))
            self._log("INFO", f"{route} 200 {latency:.0f}ms", source="app")

    def _log(self, level: str, message: str, source: str = "app") -> None:
        self.log_buffer.append(LogLine(timestamp=_now(), level=level, message=message, source=source))

    # --- read helpers ----------------------------------------------------------

    def get_recent_metrics(self, window_seconds: int) -> list[MetricPoint]:
        cutoff = _now().timestamp() - window_seconds
        return [m for m in self.metrics_history if m.timestamp.timestamp() >= cutoff]

    def get_recent_logs(self, window_seconds: int, limit: int) -> list[LogLine]:
        cutoff = _now().timestamp() - window_seconds
        recent = [log for log in self.log_buffer if log.timestamp.timestamp() >= cutoff]
        return recent[-limit:]

    def get_deployments(self) -> list[DeploymentInfo]:
        return [d.to_schema() for d in self.deployments]

    def get_state(self) -> ServiceState:
        latest = self.metrics_history[-1] if self.metrics_history else None
        return ServiceState(
            service_name=self.settings.service_name,
            replicas=self.replicas,
            active_deployment=self.active_deployment.to_schema(),
            is_degraded=self.is_degraded,
            latest_metrics=latest,
        )
