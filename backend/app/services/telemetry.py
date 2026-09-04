import asyncio
from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.enums import LogLevel
from app.models.log_entry import LogEntry
from app.models.metric_snapshot import MetricSnapshot
from app.services.alerting import evaluate_and_create_alerts
from app.services.deployment_sync import sync_deployments
from app.services.service_registry import get_or_create_service
from app.services.simulator_client import SimulatorClient

logger = get_logger(__name__)
settings = get_settings()

DEMO_SERVICE_NAME = "checkout-service"


class TelemetryPoller:
    """Polls the simulator on an interval and ingests metrics/logs/deployments.

    Tracks the last-ingested timestamp per stream in memory so repeated polls
    (which return an overlapping recent window) don't create duplicate rows.
    """

    def __init__(self, client: SimulatorClient | None = None):
        self.client = client or SimulatorClient()
        self._last_metric_ts: datetime | None = None
        self._last_log_ts: datetime | None = None

    async def poll_once(self) -> None:
        async with AsyncSessionLocal() as session:
            service = await get_or_create_service(session, DEMO_SERVICE_NAME)

            deployments = await self.client.get_deployments()
            active_deployment = await sync_deployments(session, service, deployments)
            service.last_seen_at = datetime.now(UTC)

            window_seconds = int(settings.telemetry_poll_interval_seconds * 3) + 5

            metrics = await self.client.get_recent_metrics(window_seconds=window_seconds)
            new_metrics = [
                m for m in metrics if self._is_new(m["timestamp"], self._last_metric_ts)
            ]
            for point in new_metrics:
                session.add(
                    MetricSnapshot(
                        service_id=service.id,
                        timestamp=datetime.fromisoformat(point["timestamp"]),
                        request_count=point["request_count"],
                        error_count=point["error_count"],
                        error_rate=point["error_rate"],
                        latency_p50_ms=point["latency_p50_ms"],
                        latency_p95_ms=point["latency_p95_ms"],
                        latency_p99_ms=point["latency_p99_ms"],
                    )
                )
            if new_metrics:
                self._last_metric_ts = datetime.fromisoformat(new_metrics[-1]["timestamp"])

            logs = await self.client.get_recent_logs(window_seconds=window_seconds, limit=500)
            new_logs = [log for log in logs if self._is_new(log["timestamp"], self._last_log_ts)]
            for log in new_logs:
                session.add(
                    LogEntry(
                        service_id=service.id,
                        timestamp=datetime.fromisoformat(log["timestamp"]),
                        level=LogLevel(log["level"]),
                        message=log["message"],
                        source=log["source"],
                    )
                )
            if new_logs:
                self._last_log_ts = datetime.fromisoformat(new_logs[-1]["timestamp"])

            if new_metrics:
                alerts = await evaluate_and_create_alerts(
                    session,
                    service,
                    new_metrics[-1],
                    active_deployment.id if active_deployment else None,
                    settings.error_rate_alert_threshold,
                    settings.latency_alert_threshold_ms,
                )
                if alerts:
                    logger.warning(
                        "alerts_created",
                        service=service.name,
                        count=len(alerts),
                        error_rate=new_metrics[-1]["error_rate"],
                    )

            await session.commit()

    @staticmethod
    def _is_new(timestamp_str: str, cursor: datetime | None) -> bool:
        if cursor is None:
            return True
        return datetime.fromisoformat(timestamp_str) > cursor

    def reset_cursors(self) -> None:
        self._last_metric_ts = None
        self._last_log_ts = None

    async def run_forever(self) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("telemetry_poll_failed")
            await asyncio.sleep(settings.telemetry_poll_interval_seconds)
