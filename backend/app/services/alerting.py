import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.enums import IncidentStatus, Severity
from app.models.incident import Incident
from app.models.service import Service
from app.observability.metrics import autoops_active_incidents, autoops_incidents_total

OPEN_STATUSES = (
    IncidentStatus.DETECTED,
    IncidentStatus.INVESTIGATING,
    IncidentStatus.DIAGNOSED,
    IncidentStatus.AWAITING_APPROVAL,
    IncidentStatus.REMEDIATING,
    IncidentStatus.VERIFYING,
)


def determine_severity(error_rate: float, error_threshold: float) -> Severity:
    if error_rate >= error_threshold * 3:
        return Severity.CRITICAL
    if error_rate >= error_threshold * 2:
        return Severity.HIGH
    return Severity.MEDIUM


async def get_open_incident(session: AsyncSession, service: Service) -> Incident | None:
    result = await session.execute(
        select(Incident)
        .where(Incident.service_id == service.id, Incident.status.in_(OPEN_STATUSES))
        .order_by(Incident.detected_at.desc())
    )
    return result.scalars().first()


async def evaluate_and_create_alerts(
    session: AsyncSession,
    service: Service,
    metric_point: dict[str, Any],
    triggering_deployment_id: uuid.UUID | None,
    error_rate_threshold: float,
    latency_threshold_ms: float,
) -> list[Alert]:
    """Check a single metric snapshot against alert thresholds.

    Creates (or reuses) an open incident for the service and attaches an Alert
    per breached metric. Returns the alerts created, or an empty list if the
    service is healthy.
    """
    breaches: list[tuple[str, float, float]] = []
    if metric_point["error_rate"] > error_rate_threshold:
        breaches.append(("error_rate", metric_point["error_rate"], error_rate_threshold))
    if metric_point["latency_p95_ms"] > latency_threshold_ms:
        breaches.append(("latency_p95_ms", metric_point["latency_p95_ms"], latency_threshold_ms))

    if not breaches:
        return []

    incident = await get_open_incident(session, service)
    if incident is None:
        severity = determine_severity(metric_point["error_rate"], error_rate_threshold)
        incident = Incident(
            service_id=service.id,
            title=f"Elevated error rate on {service.name}",
            description=(
                f"error_rate={metric_point['error_rate']:.2%}, "
                f"latency_p95={metric_point['latency_p95_ms']:.0f}ms"
            ),
            severity=severity,
            status=IncidentStatus.DETECTED,
            triggering_deployment_id=triggering_deployment_id,
        )
        session.add(incident)
        await session.flush()
        autoops_incidents_total.labels(severity=severity.value).inc()
        autoops_active_incidents.inc()

    alerts = []
    for metric_name, value, threshold in breaches:
        alert = Alert(
            incident_id=incident.id,
            service_id=service.id,
            metric_name=metric_name,
            value=value,
            threshold=threshold,
            message=f"{metric_name} {value:.4f} exceeded threshold {threshold:.4f}",
        )
        session.add(alert)
        alerts.append(alert)

    await session.flush()
    return alerts
