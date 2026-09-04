import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.enums import LogLevel
from app.models.incident import Incident
from app.models.log_entry import LogEntry
from app.models.metric_snapshot import MetricSnapshot
from app.models.service import Service
from app.schemas.log_entry import LogEntryRead
from app.schemas.metric_snapshot import MetricSnapshotRead
from app.schemas.service import ServiceHealth, ServiceRead
from app.services.alerting import OPEN_STATUSES

router = APIRouter(prefix="/services", tags=["services"])


async def _build_health(session: AsyncSession, service: Service) -> ServiceHealth:
    latest_metric_result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.service_id == service.id)
        .order_by(MetricSnapshot.timestamp.desc())
        .limit(1)
    )
    latest = latest_metric_result.scalar_one_or_none()

    active_incidents_result = await session.execute(
        select(func.count(Incident.id)).where(
            Incident.service_id == service.id, Incident.status.in_(OPEN_STATUSES)
        )
    )
    active_incidents = active_incidents_result.scalar_one()

    status = "unknown"
    if latest is not None:
        status = "degraded" if active_incidents > 0 else "healthy"

    return ServiceHealth(
        service=ServiceRead.model_validate(service),
        error_rate=latest.error_rate if latest else 0.0,
        latency_p95_ms=latest.latency_p95_ms if latest else 0.0,
        active_incidents=active_incidents,
        status=status,
    )


@router.get("", response_model=list[ServiceHealth])
async def list_services(session: AsyncSession = Depends(get_db)) -> list[ServiceHealth]:
    result = await session.execute(select(Service).order_by(Service.name))
    services = result.scalars().all()
    return [await _build_health(session, service) for service in services]


@router.get("/{service_id}", response_model=ServiceHealth)
async def get_service(
    service_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> ServiceHealth:
    service = await session.get(Service, service_id)
    if service is None:
        raise NotFoundError(f"Service {service_id} not found")
    return await _build_health(session, service)


@router.get("/{service_id}/metrics", response_model=list[MetricSnapshotRead])
async def get_service_metrics(
    service_id: uuid.UUID, window_seconds: int = 300, session: AsyncSession = Depends(get_db)
) -> list[MetricSnapshotRead]:
    cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
    result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.service_id == service_id, MetricSnapshot.timestamp >= cutoff)
        .order_by(MetricSnapshot.timestamp)
    )
    return [MetricSnapshotRead.model_validate(m) for m in result.scalars().all()]


@router.get("/{service_id}/logs", response_model=list[LogEntryRead])
async def get_service_logs(
    service_id: uuid.UUID,
    window_seconds: int = 300,
    limit: int = 200,
    level: LogLevel | None = None,
    session: AsyncSession = Depends(get_db),
) -> list[LogEntryRead]:
    cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
    query = select(LogEntry).where(
        LogEntry.service_id == service_id, LogEntry.timestamp >= cutoff
    )
    if level is not None:
        query = query.where(LogEntry.level == level)
    query = query.order_by(LogEntry.timestamp.desc()).limit(limit)
    result = await session.execute(query)
    entries = list(reversed(result.scalars().all()))
    return [LogEntryRead.model_validate(entry) for entry in entries]
