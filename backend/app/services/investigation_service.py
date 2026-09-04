from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.factory import get_provider
from app.core.config import get_settings
from app.core.errors import ConflictError, InvestigationFailedError
from app.core.logging import get_logger
from app.models.enums import IncidentStatus, InvestigationStatus
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.tools.executor import ToolExecutor

logger = get_logger(__name__)

INVESTIGABLE_STATUSES = (IncidentStatus.DETECTED, IncidentStatus.INVESTIGATING)


async def run_investigation(session: AsyncSession, incident: Incident) -> Investigation:
    if incident.status not in INVESTIGABLE_STATUSES:
        raise ConflictError(
            f"Incident is in status {incident.status.value}; cannot start an investigation"
        )

    settings = get_settings()
    incident.status = IncidentStatus.INVESTIGATING
    investigation = Investigation(incident_id=incident.id, llm_provider=settings.llm_provider)
    session.add(investigation)
    await session.flush()

    executor = ToolExecutor(
        session=session,
        investigation_id=investigation.id,
        service_id=incident.service_id,
        incident_id=incident.id,
    )
    provider = get_provider(settings)

    try:
        diagnosis = await provider.investigate(executor)
    except Exception as exc:
        investigation.status = InvestigationStatus.FAILED
        investigation.completed_at = datetime.now(UTC)
        await session.commit()
        logger.exception("investigation_failed", incident_id=str(incident.id))
        raise InvestigationFailedError(f"Investigation failed: {exc}") from exc

    investigation.status = InvestigationStatus.COMPLETED
    investigation.root_cause = diagnosis.root_cause
    investigation.confidence = diagnosis.confidence
    investigation.summary = diagnosis.summary
    investigation.recommended_action = (
        diagnosis.recommended_action.value if diagnosis.recommended_action else ""
    )
    investigation.completed_at = datetime.now(UTC)
    incident.status = IncidentStatus.DIAGNOSED

    await session.commit()
    await session.refresh(investigation, attribute_names=["tool_calls"])
    return investigation
