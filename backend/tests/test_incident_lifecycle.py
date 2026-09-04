import pytest

from app.core.errors import ConflictError
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.services import incident_service
from app.services.alerting import evaluate_and_create_alerts
from app.services.investigation_service import run_investigation
from app.services.postmortem_service import generate_postmortem
from tests.factories import seed_bad_deployment, seed_db_error_logs, seed_metrics


@pytest.mark.asyncio
async def test_healthy_metric_point_creates_no_incident(db_session, service):
    healthy_point = {"error_rate": 0.01, "latency_p95_ms": 80.0}
    alerts = await evaluate_and_create_alerts(
        db_session,
        service,
        healthy_point,
        None,
        error_rate_threshold=0.15,
        latency_threshold_ms=800,
    )
    assert alerts == []


@pytest.mark.asyncio
async def test_breaching_metric_point_creates_incident_and_alerts(db_session, service):
    bad_point = {"error_rate": 0.45, "latency_p95_ms": 950.0}

    alerts = await evaluate_and_create_alerts(
        db_session, service, bad_point, None, error_rate_threshold=0.15, latency_threshold_ms=800
    )

    assert len(alerts) == 2  # error_rate and latency both breached
    incident = await db_session.get(Incident, alerts[0].incident_id)
    assert incident.status == IncidentStatus.DETECTED
    assert incident.severity.value in ("HIGH", "CRITICAL")


@pytest.mark.asyncio
async def test_repeated_breaches_reuse_the_same_open_incident(db_session, service):
    bad_point = {"error_rate": 0.45, "latency_p95_ms": 950.0}

    first_alerts = await evaluate_and_create_alerts(
        db_session, service, bad_point, None, error_rate_threshold=0.15, latency_threshold_ms=800
    )
    second_alerts = await evaluate_and_create_alerts(
        db_session, service, bad_point, None, error_rate_threshold=0.15, latency_threshold_ms=800
    )

    assert first_alerts[0].incident_id == second_alerts[0].incident_id


@pytest.mark.asyncio
async def test_investigation_diagnoses_rollback_for_correlated_bad_deployment(db_session, service):
    bad_deployment = await seed_bad_deployment(db_session, service, minutes_since_deploy=2)
    await seed_db_error_logs(db_session, service, count=10, start_minutes_ago=3)
    await seed_metrics(
        db_session, service, count=5, error_rate=0.45, latency_p95_ms=900, start_minutes_ago=3
    )

    bad_point = {"error_rate": 0.45, "latency_p95_ms": 900.0}
    alerts = await evaluate_and_create_alerts(
        db_session,
        service,
        bad_point,
        bad_deployment.id,
        error_rate_threshold=0.15,
        latency_threshold_ms=800,
    )
    incident = await db_session.get(Incident, alerts[0].incident_id)

    investigation = await run_investigation(db_session, incident)

    assert investigation.recommended_action == "ROLLBACK_DEPLOYMENT"
    assert investigation.confidence > 0.5
    assert len(investigation.evidence) > 0
    assert len(investigation.tool_calls) == 5  # all 5 read-only tools called
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.DIAGNOSED


@pytest.mark.asyncio
async def test_cannot_investigate_an_already_diagnosed_incident(db_session, service):
    bad_deployment = await seed_bad_deployment(db_session, service)
    await seed_db_error_logs(db_session, service, count=5, start_minutes_ago=2)
    await seed_metrics(
        db_session, service, count=3, error_rate=0.4, latency_p95_ms=900, start_minutes_ago=2
    )
    bad_point = {"error_rate": 0.4, "latency_p95_ms": 900.0}
    alerts = await evaluate_and_create_alerts(
        db_session,
        service,
        bad_point,
        bad_deployment.id,
        error_rate_threshold=0.15,
        latency_threshold_ms=800,
    )
    incident = await db_session.get(Incident, alerts[0].incident_id)
    await run_investigation(db_session, incident)

    with pytest.raises(ConflictError):
        await run_investigation(db_session, incident)


@pytest.mark.asyncio
async def test_postmortem_generation_requires_terminal_status(db_session, service):
    bad_deployment = await seed_bad_deployment(db_session, service)
    bad_point = {"error_rate": 0.4, "latency_p95_ms": 900.0}
    alerts = await evaluate_and_create_alerts(
        db_session,
        service,
        bad_point,
        bad_deployment.id,
        error_rate_threshold=0.15,
        latency_threshold_ms=800,
    )
    incident = await incident_service.get_incident(db_session, alerts[0].incident_id)

    with pytest.raises(ConflictError):
        await generate_postmortem(db_session, incident)
