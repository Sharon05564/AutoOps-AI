"""Read-only investigation tools.

Every function here only queries the database that telemetry ingestion (see
app/services/telemetry.py) already populated from the simulator - it never
talks to the simulator directly and never mutates state. This is what makes
them safe to let an LLM call automatically without any approval gate.

Deliberately excluded from every tool's output: any "is_bad_deployment"-style
ground-truth flag. The investigation agent (mock or real LLM) has to infer the
root cause from the same observable symptoms - error rates, latency, log
contents, deployment timing - that a human on-call engineer would look at.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.deployment import Deployment
from app.models.enums import LogLevel
from app.models.incident import Incident
from app.models.log_entry import LogEntry
from app.models.metric_snapshot import MetricSnapshot
from app.models.service import Service
from app.services.alerting import OPEN_STATUSES


async def get_service_health(session: AsyncSession, service_id: uuid.UUID) -> dict[str, Any]:
    service = await session.get(Service, service_id)
    if service is None:
        return {"error": f"service {service_id} not found"}

    latest_metric_result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.service_id == service_id)
        .order_by(MetricSnapshot.timestamp.desc())
        .limit(1)
    )
    latest = latest_metric_result.scalar_one_or_none()

    active_incidents_result = await session.execute(
        select(Incident).where(
            Incident.service_id == service_id, Incident.status.in_(OPEN_STATUSES)
        )
    )
    active_incidents = active_incidents_result.scalars().all()

    active_deployment = None
    if service.active_deployment_id:
        active_deployment = await session.get(Deployment, service.active_deployment_id)

    return {
        "service_name": service.name,
        "replicas": service.replicas,
        "active_deployment_version": active_deployment.version if active_deployment else None,
        "error_rate": latest.error_rate if latest else None,
        "latency_p95_ms": latest.latency_p95_ms if latest else None,
        "active_incident_count": len(active_incidents),
    }


async def get_recent_metrics(
    session: AsyncSession, service_id: uuid.UUID, window_seconds: int = 300, limit: int = 20
) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
    result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.service_id == service_id, MetricSnapshot.timestamp >= cutoff)
        .order_by(MetricSnapshot.timestamp.desc())
        .limit(limit)
    )
    points = list(reversed(result.scalars().all()))
    return [
        {
            "timestamp": p.timestamp.isoformat(),
            "request_count": p.request_count,
            "error_count": p.error_count,
            "error_rate": p.error_rate,
            "latency_p50_ms": p.latency_p50_ms,
            "latency_p95_ms": p.latency_p95_ms,
            "latency_p99_ms": p.latency_p99_ms,
        }
        for p in points
    ]


async def get_recent_logs(
    session: AsyncSession,
    service_id: uuid.UUID,
    window_seconds: int = 300,
    limit: int = 30,
    level: str | None = None,
) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
    query = (
        select(LogEntry)
        .where(LogEntry.service_id == service_id, LogEntry.timestamp >= cutoff)
        .order_by(LogEntry.timestamp.desc())
        .limit(limit)
    )
    if level:
        query = query.where(LogEntry.level == LogLevel(level))
    result = await session.execute(query)
    entries = list(reversed(result.scalars().all()))
    return [
        {"timestamp": e.timestamp.isoformat(), "level": e.level.value, "message": e.message}
        for e in entries
    ]


async def get_recent_deployments(
    session: AsyncSession, service_id: uuid.UUID, limit: int = 5
) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Deployment)
        .where(Deployment.service_id == service_id)
        .order_by(Deployment.deployed_at.desc())
        .limit(limit)
    )
    deployments = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "version": d.version,
            "status": d.status.value,
            "deployed_at": d.deployed_at.isoformat(),
            "rolled_back_at": d.rolled_back_at.isoformat() if d.rolled_back_at else None,
        }
        for d in deployments
    ]


async def get_incident_context(session: AsyncSession, incident_id: uuid.UUID) -> dict[str, Any]:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        return {"error": f"incident {incident_id} not found"}

    service = await session.get(Service, incident.service_id)
    alerts_result = await session.execute(
        select(Alert).where(Alert.incident_id == incident_id).order_by(Alert.triggered_at)
    )
    alerts = alerts_result.scalars().all()

    return {
        "incident_id": str(incident.id),
        "service_name": service.name if service else None,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "detected_at": incident.detected_at.isoformat(),
        "alerts": [
            {
                "metric_name": a.metric_name,
                "value": a.value,
                "threshold": a.threshold,
                "triggered_at": a.triggered_at.isoformat(),
            }
            for a in alerts
        ],
    }
