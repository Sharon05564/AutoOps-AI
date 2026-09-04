import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.enums import IncidentStatus
from app.schemas.alert import AlertRead
from app.schemas.incident import IncidentDetail, IncidentRead, TimelineEvent
from app.schemas.investigation import InvestigationRead
from app.schemas.remediation import RemediationActionRead
from app.schemas.verification import VerificationRead
from app.services import incident_service

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
