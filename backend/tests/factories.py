import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Deployment
from app.models.enums import DeploymentStatus, LogLevel
from app.models.incident import Incident
from app.models.log_entry import LogEntry
from app.models.metric_snapshot import MetricSnapshot
from app.models.service import Service
from app.services.alerting import evaluate_and_create_alerts
from app.services.investigation_service import run_investigation
from app.services.simulator_client import SimulatorClient
from tests.conftest import minutes_ago

DB_ERROR_MESSAGE = "sqlalchemy.exc.TimeoutError: QueuePool limit exceeded, connection timed out"


async def seed_bad_deployment(
    session: AsyncSession, service: Service, minutes_since_deploy: float = 2.0
) -> Deployment:
    """Create a healthy deployment followed by a bad one, mimicking what the
    simulator + telemetry sync would have produced."""
    good = Deployment(
        id=uuid.uuid4(),
        service_id=service.id,
        version="v1.0.0",
        status=DeploymentStatus.SUPERSEDED,
        is_bad_deployment=False,
        deployed_at=minutes_ago(minutes_since_deploy + 30),
    )
    bad = Deployment(
        id=uuid.uuid4(),
        service_id=service.id,
        version="v1.0.1",
        status=DeploymentStatus.ACTIVE,
        is_bad_deployment=True,
        deployed_at=minutes_ago(minutes_since_deploy),
    )
    session.add_all([good, bad])
    await session.flush()
    service.active_deployment_id = bad.id
    await session.commit()
    return bad


async def seed_metrics(
    session: AsyncSession,
    service: Service,
    *,
    count: int,
    error_rate: float,
    latency_p95_ms: float,
    start_minutes_ago: float,
) -> None:
    step = start_minutes_ago / max(count, 1)
    for i in range(count):
        session.add(
            MetricSnapshot(
                service_id=service.id,
                timestamp=minutes_ago(start_minutes_ago - i * step),
                request_count=100,
                error_count=int(100 * error_rate),
                error_rate=error_rate,
                latency_p50_ms=latency_p95_ms * 0.4,
                latency_p95_ms=latency_p95_ms,
                latency_p99_ms=latency_p95_ms * 1.6,
            )
        )
    await session.commit()


async def create_detected_incident(session: AsyncSession, service: Service) -> Incident:
    """Build a DETECTED incident with data correlated enough that a real
    investigation would recommend a rollback: a bad deployment, matching DB
    error logs, and breaching metrics - but stop short of investigating it."""
    bad_deployment = await seed_bad_deployment(session, service, minutes_since_deploy=2)
    await seed_db_error_logs(session, service, count=10, start_minutes_ago=3)
    await seed_metrics(
        session, service, count=5, error_rate=0.45, latency_p95_ms=900, start_minutes_ago=3
    )

    bad_point = {"error_rate": 0.45, "latency_p95_ms": 900.0}
    alerts = await evaluate_and_create_alerts(
        session,
        service,
        bad_point,
        bad_deployment.id,
        error_rate_threshold=0.15,
        latency_threshold_ms=800,
    )
    await session.commit()
    return await session.get(Incident, alerts[0].incident_id)


async def create_diagnosed_incident(session: AsyncSession, service: Service) -> Incident:
    """Same as create_detected_incident, but also runs a real investigation
    against the seeded data so the incident is DIAGNOSED with a
    recommended_action, ready for remediation tests."""
    incident = await create_detected_incident(session, service)
    await run_investigation(session, incident)
    await session.refresh(incident, attribute_names=["investigations", "remediation_actions"])
    return incident


async def patch_successful_rollback(
    monkeypatch: pytest.MonkeyPatch, session: AsyncSession, service: Service
) -> None:
    """Stub the simulator HTTP calls a rollback makes, without a real
    simulator running: rollback_deployment reports the previous version, and
    get_deployments reflects the post-rollback state so the real
    sync_deployments() logic (unmocked) updates our DB correctly."""
    result = await session.execute(select(Deployment).where(Deployment.service_id == service.id))
    deployments = {d.status: d for d in result.scalars().all()}
    bad = deployments[DeploymentStatus.ACTIVE]
    good = deployments[DeploymentStatus.SUPERSEDED]

    async def fake_rollback_deployment(self):
        return {"version": good.version}

    async def fake_get_deployments(self):
        return [
            {
                "id": str(bad.id),
                "version": bad.version,
                "status": "ROLLED_BACK",
                "is_bad_deployment": True,
                "deployed_at": bad.deployed_at.isoformat(),
                "rolled_back_at": minutes_ago(0).isoformat(),
            },
            {
                "id": str(good.id),
                "version": good.version,
                "status": "ACTIVE",
                "is_bad_deployment": False,
                "deployed_at": good.deployed_at.isoformat(),
                "rolled_back_at": None,
            },
        ]

    monkeypatch.setattr(SimulatorClient, "rollback_deployment", fake_rollback_deployment)
    monkeypatch.setattr(SimulatorClient, "get_deployments", fake_get_deployments)


async def seed_db_error_logs(
    session: AsyncSession, service: Service, *, count: int, start_minutes_ago: float
) -> None:
    step = start_minutes_ago / max(count, 1)
    for i in range(count):
        session.add(
            LogEntry(
                service_id=service.id,
                timestamp=minutes_ago(start_minutes_ago - i * step),
                level=LogLevel.ERROR,
                message=DB_ERROR_MESSAGE,
                source="app",
            )
        )
    await session.commit()
