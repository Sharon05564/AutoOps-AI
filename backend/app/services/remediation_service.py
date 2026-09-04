from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError
from app.core.logging import get_logger
from app.models.approval import Approval
from app.models.enums import ActionType, IncidentStatus, RemediationStatus
from app.models.incident import Incident
from app.models.remediation_action import RemediationAction
from app.models.service import Service
from app.observability.metrics import (
    autoops_active_incidents,
    autoops_remediation_attempts_total,
    autoops_remediation_success_total,
)
from app.policies.risk import requires_approval, risk_level_for
from app.services.verification_service import schedule_automatic_verification
from app.tools import mutating

logger = get_logger(__name__)

IN_FLIGHT_STATUSES = (
    RemediationStatus.PENDING_APPROVAL,
    RemediationStatus.APPROVED,
    RemediationStatus.EXECUTING,
)

AUTO_VERIFICATION_DELAY_SECONDS = 10.0

ACTION_EXECUTORS = {
    ActionType.ROLLBACK_DEPLOYMENT: mutating.rollback_deployment,
    ActionType.RESTART_SERVICE: mutating.restart_service,
    ActionType.SCALE_SERVICE: mutating.scale_service,
}


async def propose_remediation(
    session: AsyncSession, incident: Incident, action_type: ActionType | None = None
) -> RemediationAction:
    """Propose a remediation action for a diagnosed incident.

    Idempotent: if an action is already pending/approved/executing for this
    incident, that same action is returned instead of creating a new one.
    Enforces a hard cap on remediation attempts per incident to prevent
    endless retry loops.
    """
    in_flight = next(
        (a for a in incident.remediation_actions if a.status in IN_FLIGHT_STATUSES), None
    )
    if in_flight is not None:
        return in_flight

    if incident.status != IncidentStatus.DIAGNOSED:
        raise ConflictError(
            f"Incident is in status {incident.status.value}; cannot propose remediation"
        )

    settings = get_settings()
    attempt_number = len(incident.remediation_actions) + 1
    if attempt_number > settings.max_remediation_attempts_per_incident:
        incident.status = IncidentStatus.FAILED
        autoops_active_incidents.dec()
        await session.commit()
        raise ConflictError("Maximum remediation attempts exceeded for this incident")

    if action_type is None:
        latest_investigation = max(
            incident.investigations, key=lambda i: i.started_at, default=None
        )
        if latest_investigation is None or not latest_investigation.recommended_action:
            raise ConflictError("No recommended action available; run an investigation first")
        action_type = ActionType(latest_investigation.recommended_action)

    risk = risk_level_for(action_type)
    parameters: dict = {}
    if action_type == ActionType.SCALE_SERVICE:
        service = await session.get(Service, incident.service_id)
        parameters = {"replicas": (service.replicas if service else 3) + 2}

    action = RemediationAction(
        incident_id=incident.id,
        action_type=action_type,
        risk_level=risk,
        status=RemediationStatus.PENDING_APPROVAL,
        parameters=parameters,
        idempotency_key=f"{incident.id}:{action_type.value}:{attempt_number}",
        attempt_number=attempt_number,
    )
    # A brand-new action has no approval yet. Set this explicitly (rather than
    # leaving the relationship untouched) so serializing the response doesn't
    # trigger an async lazy-load, which SQLAlchemy can't do outside a greenlet.
    action.approval = None
    session.add(action)
    await session.flush()

    if requires_approval(risk, settings.safe_auto_remediation):
        incident.status = IncidentStatus.AWAITING_APPROVAL
        await session.commit()
        logger.info(
            "remediation_awaiting_approval",
            incident_id=str(incident.id),
            action_type=action_type.value,
            risk=risk.value,
        )
        return action

    action.status = RemediationStatus.APPROVED
    action.approval = Approval(
        approved=True,
        approved_by="system:auto_remediation",
        reason="SAFE_AUTO_REMEDIATION enabled for this risk level",
    )
    await session.flush()
    await _execute(session, incident, action)
    return action


async def decide_approval(
    session: AsyncSession,
    incident: Incident,
    action: RemediationAction,
    approved: bool,
    approved_by: str,
    reason: str,
) -> RemediationAction:
    if action.status != RemediationStatus.PENDING_APPROVAL:
        raise ConflictError(
            f"Remediation action is in status {action.status.value}; "
            "cannot record an approval decision"
        )

    action.approval = Approval(approved=approved, approved_by=approved_by, reason=reason)

    if not approved:
        action.status = RemediationStatus.REJECTED
        incident.status = IncidentStatus.DIAGNOSED
        await session.commit()
        logger.info("remediation_rejected", incident_id=str(incident.id), by=approved_by)
        return action

    action.status = RemediationStatus.APPROVED
    await session.flush()
    await _execute(session, incident, action)
    return action


async def _execute(session: AsyncSession, incident: Incident, action: RemediationAction) -> None:
    action.status = RemediationStatus.EXECUTING
    incident.status = IncidentStatus.REMEDIATING
    await session.flush()
    autoops_remediation_attempts_total.labels(action_type=action.action_type.value).inc()

    executor = ACTION_EXECUTORS[action.action_type]
    try:
        if action.action_type == ActionType.SCALE_SERVICE:
            result = await executor(session, incident.service_id, action.parameters["replicas"])
        else:
            result = await executor(session, incident.service_id)
    except Exception as exc:
        logger.exception("remediation_execution_error", incident_id=str(incident.id))
        action.status = RemediationStatus.FAILED
        action.result = {"error": str(exc)}
        action.executed_at = datetime.now(UTC)
        incident.status = IncidentStatus.FAILED
        autoops_active_incidents.dec()
        await session.commit()
        return

    action.result = result
    action.executed_at = datetime.now(UTC)
    succeeded = bool(result.get("success"))
    action.status = RemediationStatus.SUCCEEDED if succeeded else RemediationStatus.FAILED
    incident.status = IncidentStatus.VERIFYING if succeeded else IncidentStatus.FAILED
    if succeeded:
        autoops_remediation_success_total.labels(action_type=action.action_type.value).inc()
    else:
        autoops_active_incidents.dec()
    await session.commit()
    logger.info(
        "remediation_executed",
        incident_id=str(incident.id),
        action_type=action.action_type.value,
        status=action.status.value,
    )
    if succeeded:
        schedule_automatic_verification(incident.id, delay_seconds=AUTO_VERIFICATION_DELAY_SECONDS)
