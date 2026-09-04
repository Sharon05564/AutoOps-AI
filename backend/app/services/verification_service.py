import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.enums import IncidentStatus, VerificationStatus
from app.models.incident import Incident
from app.models.metric_snapshot import MetricSnapshot
from app.models.verification import Verification

logger = get_logger(__name__)


async def _latest_metric_snapshot(
    session: AsyncSession, service_id: uuid.UUID, before: datetime | None = None
) -> MetricSnapshot | None:
    query = select(MetricSnapshot).where(MetricSnapshot.service_id == service_id)
    if before is not None:
        query = query.where(MetricSnapshot.timestamp <= before)
    query = query.order_by(MetricSnapshot.timestamp.desc()).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none()


def _snapshot_to_dict(snapshot: MetricSnapshot | None) -> dict:
    if snapshot is None:
        return {}
    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "error_rate": snapshot.error_rate,
        "latency_p95_ms": snapshot.latency_p95_ms,
        "request_count": snapshot.request_count,
    }


async def verify_recovery(session: AsyncSession, incident: Incident) -> Verification:
    """Compare metrics from just before the last remediation to right now.

    Marks the incident RESOLVED if the service is back under the alert
    thresholds, or FAILED if it is not - closing the loop the spec calls for:
    "if the error rate returns to normal, mark the remediation successful."
    """
    if incident.status != IncidentStatus.VERIFYING:
        raise ConflictError(
            f"Incident is in status {incident.status.value}; cannot verify recovery"
        )

    latest_action = max(incident.remediation_actions, key=lambda a: a.created_at, default=None)
    if latest_action is None or latest_action.executed_at is None:
        raise ConflictError("No executed remediation action to verify recovery against")

    settings = get_settings()
    before_snapshot = await _latest_metric_snapshot(
        session, incident.service_id, before=latest_action.executed_at
    )
    after_snapshot = await _latest_metric_snapshot(session, incident.service_id)

    healthy = (
        after_snapshot is not None
        and after_snapshot.error_rate <= settings.error_rate_alert_threshold
        and after_snapshot.latency_p95_ms <= settings.latency_alert_threshold_ms
    )

    verification = Verification(
        incident_id=incident.id,
        remediation_action_id=latest_action.id,
        status=VerificationStatus.PASSED if healthy else VerificationStatus.FAILED,
        metrics_before=_snapshot_to_dict(before_snapshot),
        metrics_after=_snapshot_to_dict(after_snapshot),
    )
    session.add(verification)

    incident.status = IncidentStatus.RESOLVED if healthy else IncidentStatus.FAILED
    if healthy:
        incident.resolved_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(verification)
    logger.info("recovery_verified", incident_id=str(incident.id), healthy=healthy)
    return verification


def schedule_automatic_verification(incident_id: uuid.UUID, delay_seconds: float) -> None:
    """Fire-and-forget: wait for metrics to stabilize, then verify recovery.

    Runs in its own DB session since the request that triggered the
    remediation will already have returned a response by the time this fires.
    """

    async def _run() -> None:
        await asyncio.sleep(delay_seconds)
        async with AsyncSessionLocal() as session:
            incident = await session.get(Incident, incident_id)
            if incident is None or incident.status != IncidentStatus.VERIFYING:
                return
            await session.refresh(incident, attribute_names=["remediation_actions"])
            try:
                await verify_recovery(session, incident)
            except ConflictError:
                logger.warning("auto_verification_skipped", incident_id=str(incident_id))

    asyncio.create_task(_run())
