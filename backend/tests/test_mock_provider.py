from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.agents.providers.mock import MockProvider
from app.models.enums import ActionType


class FakeExecutor:
    def __init__(self, responses: dict[str, Any]):
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    async def execute(self, tool_name: str, arguments: dict | None = None):
        self.calls.append((tool_name, arguments))
        return self.responses[tool_name]


def _incident_context(detected_at: datetime) -> dict:
    return {
        "incident_id": "11111111-1111-1111-1111-111111111111",
        "service_name": "checkout-service",
        "title": "Elevated error rate",
        "detected_at": detected_at.isoformat(),
        "alerts": [],
    }


def _health(error_rate: float) -> dict:
    return {
        "service_name": "checkout-service",
        "replicas": 3,
        "active_deployment_version": "v1.0.1",
        "error_rate": error_rate,
        "latency_p95_ms": 950.0,
        "active_incident_count": 1,
    }


def _deployment(deployed_at: datetime, version: str = "v1.0.1") -> dict:
    return {
        "id": "22222222-2222-2222-2222-222222222222",
        "version": version,
        "status": "ACTIVE",
        "deployed_at": deployed_at.isoformat(),
        "rolled_back_at": None,
    }


def _error_log(message: str, ts: datetime) -> dict:
    return {"timestamp": ts.isoformat(), "level": "ERROR", "message": message}


@pytest.mark.asyncio
async def test_recommends_rollback_when_db_errors_follow_recent_deployment():
    now = datetime.now(UTC)
    deployed_at = now - timedelta(minutes=5)

    executor = FakeExecutor(
        {
            "get_incident_context": _incident_context(now),
            "get_service_health": _health(error_rate=0.45),
            "get_recent_deployments": [_deployment(deployed_at)],
            "get_recent_logs": [
                _error_log("sqlalchemy.exc.TimeoutError: QueuePool limit exceeded", now)
                for _ in range(5)
            ],
            "get_recent_metrics": [],
        }
    )

    diagnosis = await MockProvider().investigate(executor)

    assert diagnosis.recommended_action == ActionType.ROLLBACK_DEPLOYMENT
    assert diagnosis.confidence > 0.5
    assert "v1.0.1" in diagnosis.root_cause


@pytest.mark.asyncio
async def test_recommends_restart_when_db_errors_without_recent_deployment():
    now = datetime.now(UTC)
    deployed_at = now - timedelta(hours=6)

    executor = FakeExecutor(
        {
            "get_incident_context": _incident_context(now),
            "get_service_health": _health(error_rate=0.3),
            "get_recent_deployments": [_deployment(deployed_at)],
            "get_recent_logs": [
                _error_log("psycopg2.OperationalError: connection timed out", now)
                for _ in range(4)
            ],
            "get_recent_metrics": [],
        }
    )

    diagnosis = await MockProvider().investigate(executor)

    assert diagnosis.recommended_action == ActionType.RESTART_SERVICE


@pytest.mark.asyncio
async def test_recommends_scale_when_error_rate_high_without_db_signature():
    now = datetime.now(UTC)

    executor = FakeExecutor(
        {
            "get_incident_context": _incident_context(now),
            "get_service_health": _health(error_rate=0.25),
            "get_recent_deployments": [],
            "get_recent_logs": [],
            "get_recent_metrics": [],
        }
    )

    diagnosis = await MockProvider().investigate(executor)

    assert diagnosis.recommended_action == ActionType.SCALE_SERVICE


@pytest.mark.asyncio
async def test_recommends_no_action_when_healthy():
    now = datetime.now(UTC)

    executor = FakeExecutor(
        {
            "get_incident_context": _incident_context(now),
            "get_service_health": _health(error_rate=0.01),
            "get_recent_deployments": [],
            "get_recent_logs": [],
            "get_recent_metrics": [],
        }
    )

    diagnosis = await MockProvider().investigate(executor)

    assert diagnosis.recommended_action is None
