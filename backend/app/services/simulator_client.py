from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


class SimulatorClient:
    """Thin async HTTP client for the checkout-service simulator."""

    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.simulator_url

    async def get_state(self) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get("/internal/state")
            response.raise_for_status()
            return response.json()

    async def get_recent_metrics(self, window_seconds: int = 60) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get(
                "/internal/metrics", params={"window_seconds": window_seconds}
            )
            response.raise_for_status()
            return response.json()

    async def get_recent_logs(
        self, window_seconds: int = 60, limit: int = 200
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get(
                "/internal/logs", params={"window_seconds": window_seconds, "limit": limit}
            )
            response.raise_for_status()
            return response.json()

    async def get_deployments(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get("/internal/deployments")
            response.raise_for_status()
            return response.json()

    async def trigger_bad_deployment(self) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/deployments/bad")
            response.raise_for_status()
            return response.json()

    async def rollback_deployment(self) -> dict[str, Any] | None:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/deployments/rollback")
            response.raise_for_status()
            return response.json()

    async def restart_service(self) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/restart")
            response.raise_for_status()
            return response.json()

    async def scale_service(self, replicas: int) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/scale", json={"replicas": replicas})
            response.raise_for_status()
            return response.json()

    async def reset(self) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post("/reset")
            response.raise_for_status()
            return response.json()


def get_simulator_client() -> SimulatorClient:
    return SimulatorClient()
