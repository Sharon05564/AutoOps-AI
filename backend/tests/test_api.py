import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.factories import (
    create_detected_incident,
    create_diagnosed_incident,
    patch_successful_rollback,
    seed_metrics,
)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_services_endpoint_reflects_seeded_service(client, db_session, service):
    response = await client.get("/api/services")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["service"]["name"] == "checkout-service"
    assert body[0]["status"] == "unknown"  # no metrics ingested yet


@pytest.mark.asyncio
async def test_get_unknown_incident_returns_404(client):
    response = await client.get(f"/api/incidents/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_incident_detail_and_timeline(client, db_session, service):
    incident = await create_diagnosed_incident(db_session, service)

    detail = await client.get(f"/api/incidents/{incident.id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "DIAGNOSED"
    assert len(body["investigations"]) == 1
    assert len(body["investigations"][0]["tool_calls"]) == 5
    assert body["investigations"][0]["recommended_action"] == "ROLLBACK_DEPLOYMENT"

    timeline = await client.get(f"/api/incidents/{incident.id}/timeline")
    assert timeline.status_code == 200
    event_types = [e["event_type"] for e in timeline.json()]
    assert "INCIDENT_DETECTED" in event_types
    assert "INVESTIGATION_COMPLETED" in event_types


@pytest.mark.asyncio
async def test_investigate_endpoint_produces_a_real_diagnosis(client, db_session, service):
    incident = await create_detected_incident(db_session, service)

    response = await client.post(f"/api/incidents/{incident.id}/investigate")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["recommended_action"] == "ROLLBACK_DEPLOYMENT"
    assert body["confidence"] > 0.5
    assert len(body["evidence"]) > 0


@pytest.mark.asyncio
async def test_investigate_on_already_diagnosed_incident_returns_409(client, db_session, service):
    incident = await create_diagnosed_incident(db_session, service)

    response = await client.post(f"/api/incidents/{incident.id}/investigate")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_remediate_on_undiagnosed_incident_returns_409(client, db_session, service):
    incident = await create_detected_incident(db_session, service)

    response = await client.post(f"/api/incidents/{incident.id}/remediate")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_full_remediation_approval_flow_via_api(
    client, db_session, service, monkeypatch: pytest.MonkeyPatch
):
    incident = await create_diagnosed_incident(db_session, service)
    await patch_successful_rollback(monkeypatch, db_session, service)

    remediate = await client.post(f"/api/incidents/{incident.id}/remediate")
    assert remediate.status_code == 200
    action = remediate.json()
    assert action["status"] == "PENDING_APPROVAL"
    assert action["risk_level"] == "HIGH"

    approve = await client.post(
        f"/api/incidents/{incident.id}/approve",
        json={"approved": True, "approved_by": "operator", "reason": "confirmed safe"},
    )
    assert approve.status_code == 200
    approved_action = approve.json()
    assert approved_action["status"] == "SUCCEEDED"
    assert approved_action["approval"]["approved_by"] == "operator"


@pytest.mark.asyncio
async def test_postmortem_available_after_full_resolution(
    client, db_session, service, monkeypatch: pytest.MonkeyPatch
):
    incident = await create_diagnosed_incident(db_session, service)
    await patch_successful_rollback(monkeypatch, db_session, service)
    await client.post(f"/api/incidents/{incident.id}/remediate")
    await client.post(
        f"/api/incidents/{incident.id}/approve",
        json={"approved": True, "approved_by": "operator", "reason": "confirmed safe"},
    )
    await seed_metrics(
        db_session, service, count=1, error_rate=0.01, latency_p95_ms=80, start_minutes_ago=0
    )

    verify = await client.post(f"/api/incidents/{incident.id}/verify")
    assert verify.status_code == 200
    assert verify.json()["status"] == "PASSED"

    postmortem = await client.get(f"/api/incidents/{incident.id}/postmortem")
    assert postmortem.status_code == 200
    body = postmortem.json()
    assert "v1.0.1" in body["root_cause"]
    assert len(body["prevention_recommendations"]) > 0

    markdown = await client.get(f"/api/incidents/{incident.id}/postmortem/markdown")
    assert markdown.status_code == 200
    assert "# Postmortem" in markdown.text
