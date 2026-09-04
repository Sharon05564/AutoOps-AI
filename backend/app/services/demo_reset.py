from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.log_entry import LogEntry
from app.models.metric_snapshot import MetricSnapshot
from app.models.service import Service


async def reset_demo_service(session: AsyncSession, service: Service) -> None:
    """Wipe all incident/telemetry history for a service back to a clean slate.

    Relies on ORM cascade='all, delete-orphan' on Incident's relationships to
    also remove alerts, investigations (+ tool calls), remediation actions
    (+ approvals), verifications, and postmortems.
    """
    service.active_deployment_id = None
    await session.flush()

    result = await session.execute(select(Incident).where(Incident.service_id == service.id))
    for incident in result.scalars().all():
        await session.delete(incident)
    await session.flush()

    await session.execute(delete(MetricSnapshot).where(MetricSnapshot.service_id == service.id))
    await session.execute(delete(LogEntry).where(LogEntry.service_id == service.id))
    await session.execute(delete(Deployment).where(Deployment.service_id == service.id))

    service.replicas = 3
    service.last_seen_at = None
