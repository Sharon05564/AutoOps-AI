import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.enums import IncidentStatus, RemediationStatus
from app.models.incident import Incident
from app.schemas.alert import AlertRead
from app.schemas.approval import ApprovalCreate
from app.schemas.incident import IncidentDetail, IncidentRead, TimelineEvent
from app.schemas.investigation import InvestigationDetail, InvestigationRead
from app.schemas.remediation import RemediateRequest, RemediationActionRead
from app.schemas.verification import VerificationRead
from app.services import incident_service
from app.services.investigation_service import run_investigation
from app.services.remediation_service import decide_approval, propose_remediation
from app.services.verification_service import verify_recovery

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    status: IncidentStatus | None = None, session: AsyncSession = Depends(get_db)
) -> list[IncidentRead]:
    incidents = await incident_service.list_incidents(session, status=status)
    return [IncidentRead.model_validate(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(
    incident_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> IncidentDetail:
    incident = await incident_service.get_incident(session, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")
    has_pm = await incident_service.has_postmortem(session, incident_id)
    return IncidentDetail(
        **IncidentRead.model_validate(incident).model_dump(),
        alerts=[AlertRead.model_validate(a) for a in incident.alerts],
        investigations=[InvestigationRead.model_validate(i) for i in incident.investigations],
        remediation_actions=[
            RemediationActionRead.model_validate(r) for r in incident.remediation_actions
        ],
        verifications=[VerificationRead.model_validate(v) for v in incident.verifications],
        has_postmortem=has_pm,
    )


@router.get("/{incident_id}/timeline", response_model=list[TimelineEvent])
async def get_incident_timeline(
    incident_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> list[TimelineEvent]:
    incident = await incident_service.get_incident(session, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")
    return [TimelineEvent(**event) for event in incident_service.build_timeline(incident)]


@router.post("/{incident_id}/investigate", response_model=InvestigationDetail)
async def investigate_incident(
    incident_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> InvestigationDetail:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")
    investigation = await run_investigation(session, incident)
    return InvestigationDetail.model_validate(investigation)


@router.post("/{incident_id}/remediate", response_model=RemediationActionRead)
async def remediate_incident(
    incident_id: uuid.UUID,
    request: RemediateRequest | None = None,
    session: AsyncSession = Depends(get_db),
) -> RemediationActionRead:
    incident = await incident_service.get_incident(session, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")
    action_type = request.action_type if request else None
    action = await propose_remediation(session, incident, action_type=action_type)
    return RemediationActionRead.model_validate(action)


@router.post("/{incident_id}/approve", response_model=RemediationActionRead)
async def approve_incident_remediation(
    incident_id: uuid.UUID,
    request: ApprovalCreate,
    session: AsyncSession = Depends(get_db),
) -> RemediationActionRead:
    incident = await incident_service.get_incident(session, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")

    action = next(
        (a for a in incident.remediation_actions if a.status == RemediationStatus.PENDING_APPROVAL),
        None,
    )
    if action is None:
        raise NotFoundError(f"Incident {incident_id} has no remediation action awaiting approval")

    action = await decide_approval(
        session,
        incident,
        action,
        approved=request.approved,
        approved_by=request.approved_by,
        reason=request.reason,
    )
    return RemediationActionRead.model_validate(action)


@router.post("/{incident_id}/verify", response_model=VerificationRead)
async def verify_incident_recovery(
    incident_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> VerificationRead:
    incident = await incident_service.get_incident(session, incident_id)
    if incident is None:
        raise NotFoundError(f"Incident {incident_id} not found")
    verification = await verify_recovery(session, incident)
    return VerificationRead.model_validate(verification)
