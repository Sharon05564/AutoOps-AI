"""Mutating remediation tools.

Unlike app/tools/read_only.py, these are never exposed to the investigation
agent's tool-calling loop - they are only ever invoked by
app/services/remediation_service.py, after the safety/approval policy has
cleared the action. Each one talks to the simulator over HTTP (never a shell
command) and then syncs the resulting state into our own tables.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.services.deployment_sync import sync_deployments
from app.services.simulator_client import SimulatorClient


async def rollback_deployment(
    session: AsyncSession, service_id: uuid.UUID, client: SimulatorClient | None = None
) -> dict[str, Any]:
    client = client or SimulatorClient()
    previous = await client.rollback_deployment()
    if previous is None:
        return {
            "success": False,
            "reason": "active deployment was not marked bad; nothing to roll back",
        }

    service = await session.get(Service, service_id)
    deployments = await client.get_deployments()
    await sync_deployments(session, service, deployments)
    return {"success": True, "rolled_back_to": previous.get("version")}


async def restart_service(
    session: AsyncSession, service_id: uuid.UUID, client: SimulatorClient | None = None
) -> dict[str, Any]:
    client = client or SimulatorClient()
    result = await client.restart_service()
    return {"success": True, "detail": result}


async def scale_service(
    session: AsyncSession,
    service_id: uuid.UUID,
    replicas: int,
    client: SimulatorClient | None = None,
) -> dict[str, Any]:
    client = client or SimulatorClient()
    result = await client.scale_service(replicas)

    service = await session.get(Service, service_id)
    if service is not None:
        service.replicas = result["replicas"]

    return {"success": True, "replicas": result["replicas"]}
