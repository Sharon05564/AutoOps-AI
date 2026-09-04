from datetime import datetime
from typing import Any

from app.agents.providers.base import InvestigationProvider
from app.agents.schemas import Diagnosis, PostmortemNarrative
from app.models.enums import ActionType
from app.tools.executor import ToolExecutor

DB_ERROR_KEYWORDS = [
    "connection",
    "timeout",
    "pool",
    "operationalerror",
    "toomanyconnections",
    "too many connections",
]

RECENT_DEPLOYMENT_WINDOW_MINUTES = 15


class MockProvider(InvestigationProvider):
    """Deterministic, rule-based provider - no API key required.

    Calls the same read-only tools a real LLM would and reasons over their
    actual outputs (log content, deployment timing, error rate) rather than
    returning a canned diagnosis. This keeps the demo runnable and
    reproducible with zero external dependencies while still exercising the
    full tool-calling / evidence-gathering pipeline.
    """

    name = "mock"

    async def investigate(self, executor: ToolExecutor) -> Diagnosis:
        incident = await executor.execute("get_incident_context")
        health = await executor.execute("get_service_health")
        deployments = await executor.execute("get_recent_deployments")
        error_logs = await executor.execute(
            "get_recent_logs", {"window_seconds": 600, "level": "ERROR"}
        )
        await executor.execute("get_recent_metrics", {"window_seconds": 300})

        db_error_logs = [
            log
            for log in error_logs
            if any(keyword in log["message"].lower() for keyword in DB_ERROR_KEYWORDS)
        ]

        latest_deployment = deployments[0] if deployments else None
        deployment_is_recent = False
        minutes_since_deploy: float | None = None
        if latest_deployment and incident.get("detected_at"):
            detected_at = datetime.fromisoformat(incident["detected_at"])
            deployed_at = datetime.fromisoformat(latest_deployment["deployed_at"])
            minutes_since_deploy = (detected_at - deployed_at).total_seconds() / 60
            deployment_is_recent = 0 <= minutes_since_deploy <= RECENT_DEPLOYMENT_WINDOW_MINUTES

        error_rate = health.get("error_rate") or 0.0
        evidence = [
            f"{len(db_error_logs)} of {len(error_logs)} recent ERROR logs mention database "
            "connection/timeout failures.",
            f"Current error rate is {error_rate:.1%} on {health.get('service_name')}.",
        ]
        if latest_deployment:
            evidence.append(
                f"Most recent deployment {latest_deployment['version']} went out "
                f"{minutes_since_deploy:.1f} minutes before this incident was detected."
                if minutes_since_deploy is not None
                else f"Most recent deployment is {latest_deployment['version']}."
            )

        if db_error_logs and deployment_is_recent:
            return Diagnosis(
                root_cause=(
                    f"Deployment {latest_deployment['version']} likely introduced a database "
                    "connectivity regression: connection/timeout errors began appearing "
                    "shortly after it went out."
                ),
                confidence=min(0.95, 0.55 + 0.05 * len(db_error_logs)),
                summary=(
                    f"{health.get('service_name')} is returning database connection errors on "
                    f"{error_rate:.1%} of requests, correlated with deployment "
                    f"{latest_deployment['version']}."
                ),
                recommended_action=ActionType.ROLLBACK_DEPLOYMENT,
                evidence=evidence,
            )

        if db_error_logs:
            return Diagnosis(
                root_cause=(
                    "Database connection/timeout errors are elevated but do not correlate with "
                    "a recent deployment - likely a transient infrastructure issue."
                ),
                confidence=0.4,
                summary=f"{health.get('service_name')} is seeing database connection errors.",
                recommended_action=ActionType.RESTART_SERVICE,
                evidence=evidence,
            )

        if error_rate > 0.15:
            return Diagnosis(
                root_cause=(
                    "Error rate is elevated without a clear database-error signature - "
                    "possibly a capacity issue."
                ),
                confidence=0.3,
                summary=f"{health.get('service_name')} has an elevated error rate.",
                recommended_action=ActionType.SCALE_SERVICE,
                evidence=evidence,
            )

        return Diagnosis(
            root_cause="No clear anomaly found in the available signals.",
            confidence=0.2,
            summary=f"{health.get('service_name')} looks healthy based on current data.",
            recommended_action=None,
            evidence=evidence,
        )

    async def generate_postmortem_narrative(self, context: dict[str, Any]) -> PostmortemNarrative:
        root_cause = (context.get("root_cause") or "").lower()
        service_name = context.get("service_name", "the service")
        severity = context.get("severity", "UNKNOWN")
        action_type = context.get("action_type")
        verification_status = context.get("verification_status")

        outcome = (
            "recovery was confirmed"
            if verification_status == "PASSED"
            else "the fix did not resolve the issue and further action was required"
            if verification_status == "FAILED"
            else "recovery has not yet been verified"
        )
        summary = (
            f"A {severity} severity incident degraded {service_name} "
            f"({context.get('root_cause', 'root cause unknown')}). "
            f"{action_type or 'A remediation'} was applied and {outcome}."
        )

        if "database" in root_cause or "connection" in root_cause:
            recommendations = [
                "Add a pre-deploy check that validates the DB connection pool size against "
                "expected replica count before promoting a deployment.",
                "Add a canary stage that runs synthetic checkout requests for a few minutes "
                "before shifting full traffic to a new deployment.",
                "Alert when error rate crosses threshold within 5 minutes of a deployment, "
                "tagged with the deployment version, to speed up correlation.",
            ]
        else:
            recommendations = [
                "Add an automated rollback trigger for error-rate spikes that correlate with "
                "a recent deployment.",
                "Review alert thresholds for this service to catch this class of degradation "
                "earlier.",
            ]

        if action_type in ("RESTART_SERVICE", "SCALE_SERVICE") and verification_status == "FAILED":
            recommendations.append(
                "Update the on-call runbook to prefer rollback over restart/scale when errors "
                "are correlated with a recent deployment."
            )

        return PostmortemNarrative(summary=summary, prevention_recommendations=recommendations)
