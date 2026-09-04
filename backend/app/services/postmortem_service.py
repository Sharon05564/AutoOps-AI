import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.factory import get_provider
from app.core.config import get_settings
from app.core.errors import ConflictError
from app.core.logging import get_logger
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.postmortem import Postmortem
from app.models.remediation_action import RemediationAction
from app.models.verification import Verification
from app.services import incident_service
from app.services.postmortem_markdown import render_markdown

logger = get_logger(__name__)

POSTMORTEM_ELIGIBLE_STATUSES = (IncidentStatus.RESOLVED, IncidentStatus.FAILED)


def _describe_remediation(action: RemediationAction | None) -> str:
    if action is None:
        return "No remediation action was taken."
    approver = action.approval.approved_by if action.approval else "no approval on record"
    return (
        f"{action.action_type.value} was proposed (risk: {action.risk_level.value}), "
        f"approved by {approver}, and reported status {action.status.value}."
    )


def _describe_verification(verification: Verification | None) -> str:
    if verification is None:
        return "Recovery was not verified."
    before = verification.metrics_before.get("error_rate")
    after = verification.metrics_after.get("error_rate")
    if before is None or after is None:
        return f"Verification result: {verification.status.value}."
    return (
        f"Verification {verification.status.value.lower()}: error rate went from "
        f"{before:.1%} to {after:.1%} after remediation."
    )


def _build_context(incident: Incident) -> dict[str, Any]:
    investigation = max(incident.investigations, key=lambda i: i.started_at, default=None)
    remediation = max(incident.remediation_actions, key=lambda a: a.created_at, default=None)
    verification = max(incident.verifications, key=lambda v: v.checked_at, default=None)

    return {
        "service_name": incident.service.name if incident.service else "unknown",
        "title": incident.title,
        "severity": incident.severity.value,
        "detected_at": incident.detected_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "root_cause": investigation.root_cause if investigation else "Unknown",
        "confidence": investigation.confidence if investigation else 0.0,
        "evidence": investigation.evidence if investigation else [],
        "action_type": remediation.action_type.value if remediation else None,
        "action_status": remediation.status.value if remediation else None,
        "verification_status": verification.status.value if verification else None,
    }


async def get_existing_postmortem(
    session: AsyncSession, incident_id: uuid.UUID
) -> Postmortem | None:
    result = await session.execute(
        select(Postmortem).where(Postmortem.incident_id == incident_id)
    )
    return result.scalar_one_or_none()


async def generate_postmortem(session: AsyncSession, incident: Incident) -> Postmortem:
    existing = await get_existing_postmortem(session, incident.id)
    if existing is not None:
        return existing

    if incident.status not in POSTMORTEM_ELIGIBLE_STATUSES:
        raise ConflictError(
            f"Incident is in status {incident.status.value}; a postmortem can only be "
            "generated once the incident is RESOLVED or FAILED"
        )

    investigation = max(incident.investigations, key=lambda i: i.started_at, default=None)
    remediation = max(incident.remediation_actions, key=lambda a: a.created_at, default=None)
    verification = max(incident.verifications, key=lambda v: v.checked_at, default=None)

    settings = get_settings()
    provider = get_provider(settings)
    narrative = await provider.generate_postmortem_narrative(_build_context(incident))

    timeline = [
        {**event, "timestamp": event["timestamp"].isoformat()}
        for event in incident_service.build_timeline(incident)
    ]

    postmortem = Postmortem(
        incident_id=incident.id,
        summary=narrative.summary,
        root_cause=investigation.root_cause if investigation else "Unknown",
        timeline=timeline,
        evidence=investigation.evidence if investigation else [],
        remediation_summary=_describe_remediation(remediation),
        recovery_verification=_describe_verification(verification),
        prevention_recommendations=narrative.prevention_recommendations,
        markdown_report="",
        generated_at=datetime.now(UTC),
    )
    postmortem.markdown_report = render_markdown(incident, postmortem)

    session.add(postmortem)
    await session.commit()
    await session.refresh(postmortem)
    logger.info("postmortem_generated", incident_id=str(incident.id))
    return postmortem
