import pytest

from app.core.errors import ConflictError
from app.models.enums import IncidentStatus, VerificationStatus
from app.services.remediation_service import decide_approval, propose_remediation
from app.services.verification_service import verify_recovery
from tests.factories import create_diagnosed_incident, patch_successful_rollback, seed_metrics


async def _remediate_and_approve(db_session, service, monkeypatch):
    incident = await create_diagnosed_incident(db_session, service)
    action = await propose_remediation(db_session, incident)
    await patch_successful_rollback(monkeypatch, db_session, service)
    await decide_approval(
        db_session, incident, action, approved=True, approved_by="operator", reason="ok"
    )
    # propose_remediation() doesn't append to incident.remediation_actions in
    # memory (it only sets the FK), so refresh before verify_recovery() reads
    # that collection - mirroring what the real auto-verification path does.
    await db_session.refresh(incident, attribute_names=["remediation_actions"])
    return incident


@pytest.mark.asyncio
async def test_verify_recovery_passes_when_metrics_return_to_normal(
    db_session, service, monkeypatch: pytest.MonkeyPatch
):
    incident = await _remediate_and_approve(db_session, service, monkeypatch)
    await seed_metrics(
        db_session, service, count=1, error_rate=0.01, latency_p95_ms=75, start_minutes_ago=0
    )

    verification = await verify_recovery(db_session, incident)

    assert verification.status == VerificationStatus.PASSED
    assert verification.metrics_before["error_rate"] > 0.15
    assert verification.metrics_after["error_rate"] < 0.05
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.RESOLVED
    assert incident.resolved_at is not None


@pytest.mark.asyncio
async def test_verify_recovery_fails_when_metrics_are_still_bad(
    db_session, service, monkeypatch: pytest.MonkeyPatch
):
    incident = await _remediate_and_approve(db_session, service, monkeypatch)
    await seed_metrics(
        db_session, service, count=1, error_rate=0.4, latency_p95_ms=900, start_minutes_ago=0
    )

    verification = await verify_recovery(db_session, incident)

    assert verification.status == VerificationStatus.FAILED
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.FAILED
    assert incident.resolved_at is None


@pytest.mark.asyncio
async def test_verify_recovery_rejects_incident_not_in_verifying_state(db_session, service):
    incident = await create_diagnosed_incident(db_session, service)

    with pytest.raises(ConflictError):
        await verify_recovery(db_session, incident)
