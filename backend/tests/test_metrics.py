from prometheus_client import generate_latest

from app.observability import metrics


def test_metrics_are_registered_and_exposed():
    metrics.autoops_incidents_total.labels(severity="HIGH").inc()
    metrics.autoops_active_incidents.inc()
    metrics.autoops_agent_tool_calls_total.labels(tool_name="get_service_health").inc()
    metrics.autoops_remediation_attempts_total.labels(action_type="ROLLBACK_DEPLOYMENT").inc()
    metrics.autoops_remediation_success_total.labels(action_type="ROLLBACK_DEPLOYMENT").inc()
    metrics.autoops_incident_resolution_seconds.observe(42.0)

    output = generate_latest().decode()

    assert "autoops_incidents_total" in output
    assert "autoops_active_incidents" in output
    assert "autoops_agent_tool_calls_total" in output
    assert "autoops_remediation_attempts_total" in output
    assert "autoops_remediation_success_total" in output
    assert "autoops_incident_resolution_seconds" in output
