from app.models.incident import Incident
from app.models.postmortem import Postmortem


def render_markdown(incident: Incident, postmortem: Postmortem) -> str:
    lines = [
        f"# Postmortem: {incident.title}",
        "",
        f"**Service:** {incident.service.name if incident.service else 'unknown'}  ",
        f"**Severity:** {incident.severity.value}  ",
        f"**Status:** {incident.status.value}  ",
        f"**Detected:** {incident.detected_at.isoformat()}  ",
        f"**Resolved:** {incident.resolved_at.isoformat() if incident.resolved_at else 'n/a'}  ",
        "",
        "## Summary",
        "",
        postmortem.summary,
        "",
        "## Root Cause",
        "",
        postmortem.root_cause,
        "",
        "## Evidence",
        "",
    ]
    if postmortem.evidence:
        lines.extend(f"- {item}" for item in postmortem.evidence)
    else:
        lines.append("- No evidence recorded.")

    lines += ["", "## Timeline", ""]
    for event in postmortem.timeline:
        lines.append(f"- `{event['timestamp']}` **{event['event_type']}** - {event['title']}")

    lines += [
        "",
        "## Remediation",
        "",
        postmortem.remediation_summary,
        "",
        "## Recovery Verification",
        "",
        postmortem.recovery_verification,
        "",
        "## Prevention Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in postmortem.prevention_recommendations)

    lines += ["", f"_Generated {postmortem.generated_at.isoformat()}_"]

    return "\n".join(lines)
