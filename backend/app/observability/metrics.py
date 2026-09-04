from prometheus_client import Counter, Gauge, Histogram

autoops_incidents_total = Counter(
    "autoops_incidents_total", "Total incidents detected", ["severity"]
)

autoops_active_incidents = Gauge(
    "autoops_active_incidents", "Incidents currently open (not RESOLVED or FAILED)"
)

autoops_agent_tool_calls_total = Counter(
    "autoops_agent_tool_calls_total",
    "Total investigation tool calls made by the agent",
    ["tool_name"],
)

autoops_remediation_attempts_total = Counter(
    "autoops_remediation_attempts_total", "Total remediation actions executed", ["action_type"]
)

autoops_remediation_success_total = Counter(
    "autoops_remediation_success_total",
    "Total remediation actions that executed successfully",
    ["action_type"],
)

autoops_incident_resolution_seconds = Histogram(
    "autoops_incident_resolution_seconds",
    "Time from incident detection to resolution, in seconds",
    buckets=(10, 30, 60, 120, 300, 600, 1200, 3600),
)
