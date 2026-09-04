"""End-to-end integration test for the core demo scenario:

bad deployment -> alert -> incident -> investigation -> diagnosis ->
approval -> rollback -> verification -> resolved -> postmortem

Runs entirely through the public API (httpx against the real ASGI app) and a
real Postgres database. The only thing stubbed is the simulator's HTTP
responses for the rollback call itself - everything else (alert evaluation,
the investigation agent's tool-calling loop over real DB data, the safety/
approval policy, recovery verification, and postmortem generation) is the
genuine, unmodified code path.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.factories import (
    create_detected_incident,
    patch_successful_rollback,
    seed_metrics,
)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_full_incident_response_lifecycle(
    client, db_session, service, monkeypatch: pytest.MonkeyPatch
):
    # 1. A bad deployment has gone out and telemetry has already detected it,
    #    creating an incident and alerts (this step mirrors what
    #    TelemetryPoller does automatically against the real simulator).
    incident = await create_detected_incident(db_session, service)
    incident_id = str(incident.id)

    detected = await client.get(f"/api/incidents/{incident_id}")
    assert detected.json()["status"] == "DETECTED"
    assert len(detected.json()["alerts"]) > 0

    # 2. Investigate: the agent gathers real evidence and produces a diagnosis.
    investigation = await client.post(f"/api/incidents/{incident_id}/investigate")
    assert investigation.status_code == 200
    diagnosis = investigation.json()
    assert diagnosis["status"] == "COMPLETED"
    assert diagnosis["recommended_action"] == "ROLLBACK_DEPLOYMENT"
    assert diagnosis["confidence"] > 0.5
    assert any("v1.0.1" in item for item in diagnosis["evidence"])

    after_diagnosis = await client.get(f"/api/incidents/{incident_id}")
    assert after_diagnosis.json()["status"] == "DIAGNOSED"

    # 3. Propose remediation: rollback is HIGH risk, so it must wait for approval.
    remediate = await client.post(f"/api/incidents/{incident_id}/remediate")
    assert remediate.status_code == 200
    action = remediate.json()
    assert action["action_type"] == "ROLLBACK_DEPLOYMENT"
    assert action["risk_level"] == "HIGH"
    assert action["status"] == "PENDING_APPROVAL"

    awaiting = await client.get(f"/api/incidents/{incident_id}")
    assert awaiting.json()["status"] == "AWAITING_APPROVAL"

    # 4. A human approves it. The simulator's rollback call is stubbed here -
    #    everything downstream (DB sync, status transitions) is real.
    await patch_successful_rollback(monkeypatch, db_session, service)
    approve = await client.post(
        f"/api/incidents/{incident_id}/approve",
        json={"approved": True, "approved_by": "sre-on-call", "reason": "confirmed safe rollback"},
    )
    assert approve.status_code == 200
    approved_action = approve.json()
    assert approved_action["status"] == "SUCCEEDED"
    assert approved_action["result"]["rolled_back_to"] == "v1.0.0"
    assert approved_action["approval"]["approved_by"] == "sre-on-call"

    remediating = await client.get(f"/api/incidents/{incident_id}")
    assert remediating.json()["status"] == "VERIFYING"

    # 5. AutoOps monitors metrics after the rollback - simulate them
    #    returning to normal, then verify recovery.
    await seed_metrics(
        db_session, service, count=1, error_rate=0.01, latency_p95_ms=75, start_minutes_ago=0
    )
    verify = await client.post(f"/api/incidents/{incident_id}/verify")
    assert verify.status_code == 200
    verification = verify.json()
    assert verification["status"] == "PASSED"
    assert verification["metrics_before"]["error_rate"] > 0.15
    assert verification["metrics_after"]["error_rate"] < 0.05

    resolved = await client.get(f"/api/incidents/{incident_id}")
    resolved_body = resolved.json()
    assert resolved_body["status"] == "RESOLVED"
    assert resolved_body["resolved_at"] is not None
    assert resolved_body["has_postmortem"] is False

    # 6. Generate the postmortem and confirm it's grounded in what actually
    #    happened, not templated filler.
    postmortem = await client.get(f"/api/incidents/{incident_id}/postmortem")
    assert postmortem.status_code == 200
    report = postmortem.json()
    assert "v1.0.1" in report["root_cause"]
    assert "ROLLBACK_DEPLOYMENT" in report["remediation_summary"]
    assert "sre-on-call" in report["remediation_summary"]
    assert len(report["timeline"]) >= 5
    assert len(report["prevention_recommendations"]) > 0

    markdown = await client.get(f"/api/incidents/{incident_id}/postmortem/markdown")
    assert markdown.status_code == 200
    assert "# Postmortem" in markdown.text
    assert "ROLLBACK_DEPLOYMENT" in markdown.text

    final = await client.get(f"/api/incidents/{incident_id}")
    assert final.json()["has_postmortem"] is True
