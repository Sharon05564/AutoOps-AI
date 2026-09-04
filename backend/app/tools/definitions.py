"""JSON schemas for the read-only investigation tools.

Shared by every provider: the mock provider uses these purely for logging
what "would" be sent to a model, while the OpenAI/Anthropic providers pass
them straight through as function/tool definitions.
"""

READ_ONLY_TOOLS = [
    {
        "name": "get_service_health",
        "description": (
            "Get current health snapshot for a service: replicas, active deployment "
            "version, latest error rate and p95 latency, and count of open incidents."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_recent_metrics",
        "description": (
            "Get recent metric snapshots (request/error counts, latency percentiles) "
            "for the service over a time window."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "window_seconds": {
                    "type": "integer",
                    "description": "How many seconds of history to return.",
                    "default": 300,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_recent_logs",
        "description": (
            "Get recent application log lines for the service over a time window, "
            "optionally filtered by level."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "window_seconds": {
                    "type": "integer",
                    "description": "How many seconds of history to return.",
                    "default": 300,
                },
                "level": {
                    "type": "string",
                    "description": "Optional log level filter, e.g. ERROR.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_recent_deployments",
        "description": "Get the recent deployment history for the service, most recent first.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_incident_context",
        "description": (
            "Get the full context of the incident being investigated: description, "
            "severity, and every alert that fired."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
