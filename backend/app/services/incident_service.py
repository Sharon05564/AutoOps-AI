import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.postmortem import Postmortem
from app.models.remediation_action import RemediationAction


def _detail_query():
    return select(Incident).options(
        selectinload(Incident.service),
        selectinload(Incident.alerts),
        selectinload(Incident.investigations).selectinload(Investigation.tool_calls),
        selectinload(Incident.remediation_actions).selectinload(RemediationAction.approval),
        selectinload(Incident.verifications),
    )


async def list_incidents(
    session: AsyncSession, status: IncidentStatus | None = None, limit: int = 100
) -> list[Incident]:
    query = select(Incident).order_by(Incident.detected_at.desc()).limit(limit)
    if status is not None:
        query = query.where(Incident.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_incident(session: AsyncSession, incident_id: uuid.UUID) -> Incident | None:
    result = await session.execute(_detail_query().where(Incident.id == incident_id))
    return result.unique().scalar_one_or_none()


async def has_postmortem(session: AsyncSession, incident_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Postmortem.id).where(Postmortem.incident_id == incident_id)
    )
    return result.scalar_one_or_none() is not None


def build_timeline(incident: Incident) -> list[dict]:
    """Flatten every recorded event on an incident into a chronological list."""
    events: list[dict] = [
        {
            "timestamp": incident.detected_at,
            "event_type": "INCIDENT_DETECTED",
            "title": incident.title,
            "description": incident.description,
            "metadata": {"severity": incident.severity.value},
        }
    ]

    for alert in incident.alerts:
        events.append(
            {
                "timestamp": alert.triggered_at,
                "event_type": "ALERT",
                "title": f"Alert: {alert.metric_name}",
                "description": alert.message,
                "metadata": {"value": alert.value, "threshold": alert.threshold},
            }
        )

    for investigation in incident.investigations:
        events.append(
            {
                "timestamp": investigation.started_at,
                "event_type": "INVESTIGATION_STARTED",
                "title": f"Investigation started ({investigation.llm_provider})",
                "description": "",
                "metadata": {},
            }
        )
        if investigation.completed_at:
            events.append(
                {
                    "timestamp": investigation.completed_at,
                    "event_type": "INVESTIGATION_COMPLETED",
                    "title": "Diagnosis reached",
                    "description": investigation.root_cause,
                    "metadata": {
                        "confidence": investigation.confidence,
                        "recommended_action": investigation.recommended_action,
                    },
                }
            )

    for action in incident.remediation_actions:
        events.append(
            {
                "timestamp": action.created_at,
                "event_type": "REMEDIATION_PROPOSED",
                "title": f"Proposed action: {action.action_type.value}",
                "description": f"risk={action.risk_level.value}",
                "metadata": {"status": action.status.value},
            }
        )
        if action.approval:
            events.append(
                {
                    "timestamp": action.approval.decided_at,
                    "event_type": "APPROVAL_DECIDED",
                    "title": "Approved" if action.approval.approved else "Rejected",
                    "description": action.approval.reason,
                    "metadata": {"approved_by": action.approval.approved_by},
                }
            )
        if action.executed_at:
            events.append(
                {
                    "timestamp": action.executed_at,
                    "event_type": "REMEDIATION_EXECUTED",
                    "title": f"Executed: {action.action_type.value}",
                    "description": "",
                    "metadata": {"status": action.status.value},
                }
            )

    for verification in incident.verifications:
        events.append(
            {
                "timestamp": verification.checked_at,
                "event_type": "VERIFICATION",
                "title": f"Recovery verification: {verification.status.value}",
                "description": "",
                "metadata": {},
            }
        )

    if incident.resolved_at:
        events.append(
            {
                "timestamp": incident.resolved_at,
                "event_type": "INCIDENT_RESOLVED",
                "title": "Incident resolved",
                "description": "",
                "metadata": {"status": incident.status.value},
            }
        )

    events.sort(key=lambda e: e["timestamp"])
    return events
