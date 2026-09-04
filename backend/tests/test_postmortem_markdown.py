import uuid
from datetime import UTC, datetime

from app.models.enums import IncidentStatus, Severity
from app.models.incident import Incident
from app.models.postmortem import Postmortem
from app.services.postmortem_markdown import render_markdown


def make_incident() -> Incident:
    return Incident(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        title="Elevated error rate",
        description="",
        severity=Severity.HIGH,
        status=IncidentStatus.RESOLVED,
        detected_at=datetime(2026, 1, 1, tzinfo=UTC),
        resolved_at=datetime(2026, 1, 1, 0, 10, tzinfo=UTC),
    )


def make_postmortem(incident: Incident, evidence: list[str]) -> Postmortem:
    return Postmortem(
        incident_id=incident.id,
        summary="Summary text",
        root_cause="Root cause text",
        timeline=[
            {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "event_type": "INCIDENT_DETECTED",
                "title": "Detected",
            }
        ],
        evidence=evidence,
        remediation_summary="Rolled back.",
        recovery_verification="Error rate dropped to 0%.",
        prevention_recommendations=["Add a canary stage."],
        markdown_report="",
        generated_at=datetime(2026, 1, 1, 0, 15, tzinfo=UTC),
    )


def test_render_markdown_includes_all_sections():
    incident = make_incident()
    postmortem = make_postmortem(incident, ["Evidence item one."])

    markdown = render_markdown(incident, postmortem)

    assert "# Postmortem: Elevated error rate" in markdown
    assert "## Summary" in markdown
    assert "## Root Cause" in markdown
    assert "## Evidence" in markdown
    assert "Evidence item one." in markdown
    assert "## Timeline" in markdown
    assert "## Remediation" in markdown
    assert "## Recovery Verification" in markdown
    assert "## Prevention Recommendations" in markdown
    assert "Add a canary stage." in markdown


def test_render_markdown_handles_empty_evidence():
    incident = make_incident()
    postmortem = make_postmortem(incident, [])

    markdown = render_markdown(incident, postmortem)

    assert "No evidence recorded." in markdown
