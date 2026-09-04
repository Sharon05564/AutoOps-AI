import pytest

from app.core.config import get_settings
from app.core.errors import ConflictError
from app.models.enums import ActionType, IncidentStatus, RemediationStatus, Severity
from app.models.incident import Incident
from app.services.remediation_service import decide_approval, propose_remediation
from app.services.simulator_client import SimulatorClient
from tests.factories import create_diagnosed_incident, patch_successful_rollback


@pytest.fixture
def with_safe_auto_remediation(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SAFE_AUTO_REMEDIATION", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def with_max_attempts_of_one(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MAX_REMEDIATION_ATTEMPTS_PER_INCIDENT", "1")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_high_risk_action_requires_approval_and_does_not_auto_execute(db_session, service):
    incident = await create_diagnosed_incident(db_session, service)

    action = await propose_remediation(db_session, incident)

    assert action.action_type == ActionType.ROLLBACK_DEPLOYMENT
    assert action.risk_level.value == "HIGH"
    assert action.status == RemediationStatus.PENDING_APPROVAL
    assert action.approval is None
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_medium_risk_auto_executes_when_safe_auto_remediation_enabled(
    db_session, service, with_safe_auto_remediation, monkeypatch: pytest.MonkeyPatch
):
    incident = await create_diagnosed_incident(db_session, service)

    async def fake_restart(self):
        return {"status": "restarted"}

    monkeypatch.setattr(SimulatorClient, "restart_service", fake_restart)

    action = await propose_remediation(db_session, incident, action_type=ActionType.RESTART_SERVICE)

    assert action.status == RemediationStatus.SUCCEEDED
    assert action.approval.approved_by == "system:auto_remediation"
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.VERIFYING


@pytest.mark.asyncio
async def test_medium_risk_requires_approval_when_safe_auto_remediation_disabled(
    db_session, service
):
    incident = await create_diagnosed_incident(db_session, service)

    action = await propose_remediation(db_session, incident, action_type=ActionType.RESTART_SERVICE)

    assert action.status == RemediationStatus.PENDING_APPROVAL
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_second_remediate_call_is_idempotent(db_session, service):
    incident = await create_diagnosed_incident(db_session, service)

    first = await propose_remediation(db_session, incident)
    # propose_remediation() sets incident.status directly (visible immediately
    # on this shared object) but doesn't append to incident.remediation_actions
    # (only sets the new row's FK) - refresh so the second call's in-flight
    # check sees it, exactly as a fresh per-request fetch would in the API.
    await db_session.refresh(incident, attribute_names=["remediation_actions"])
    second = await propose_remediation(db_session, incident)

    assert first.id == second.id
    assert first.attempt_number == 1


@pytest.mark.asyncio
async def test_rejecting_remediation_returns_incident_to_diagnosed(db_session, service):
    incident = await create_diagnosed_incident(db_session, service)
    action = await propose_remediation(db_session, incident)

    rejected = await decide_approval(
        db_session, incident, action, approved=False, approved_by="operator", reason="not yet"
    )

    assert rejected.status == RemediationStatus.REJECTED
    assert rejected.approval.approved is False
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.DIAGNOSED


@pytest.mark.asyncio
async def test_approving_high_risk_action_executes_rollback_and_moves_to_verifying(
    db_session, service, monkeypatch: pytest.MonkeyPatch
):
    incident = await create_diagnosed_incident(db_session, service)
    action = await propose_remediation(db_session, incident)
    await patch_successful_rollback(monkeypatch, db_session, service)

    approved = await decide_approval(
        db_session, incident, action, approved=True, approved_by="operator", reason="looks safe"
    )

    assert approved.status == RemediationStatus.SUCCEEDED
    assert approved.result["success"] is True
    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.VERIFYING


@pytest.mark.asyncio
async def test_max_remediation_attempts_exceeded_fails_the_incident(
    db_session, service, with_max_attempts_of_one
):
    incident = await create_diagnosed_incident(db_session, service)
    action = await propose_remediation(db_session, incident)
    await decide_approval(
        db_session, incident, action, approved=False, approved_by="operator", reason="reconsider"
    )
    await db_session.refresh(incident, attribute_names=["remediation_actions"])

    with pytest.raises(ConflictError, match="Maximum remediation attempts"):
        await propose_remediation(db_session, incident)

    await db_session.refresh(incident)
    assert incident.status == IncidentStatus.FAILED


@pytest.mark.asyncio
async def test_cannot_propose_remediation_before_incident_is_diagnosed(db_session, service):
    incident = Incident(
        service_id=service.id,
        title="Elevated error rate",
        severity=Severity.HIGH,
        status=IncidentStatus.DETECTED,
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident, attribute_names=["remediation_actions", "investigations"])

    with pytest.raises(ConflictError):
        await propose_remediation(db_session, incident)
