import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import Deployment
from app.models.enums import DeploymentStatus
from app.models.service import Service


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


async def sync_deployments(
    session: AsyncSession, service: Service, simulator_deployments: list[dict[str, Any]]
) -> Deployment | None:
    """Mirror the simulator's deployment history into our Deployment table.

    The simulator's deployment id is reused as our primary key, so a single
    deployment has one identity across both systems.
    """
    active_deployment: Deployment | None = None

    for raw in simulator_deployments:
        deployment_id = uuid.UUID(raw["id"])
        deployment = await session.get(Deployment, deployment_id)
        status = DeploymentStatus(raw["status"])

        if deployment is None:
            deployment = Deployment(
                id=deployment_id,
                service_id=service.id,
                version=raw["version"],
                status=status,
                is_bad_deployment=raw["is_bad_deployment"],
                deployed_at=_parse_dt(raw["deployed_at"]),
                rolled_back_at=_parse_dt(raw.get("rolled_back_at")),
            )
            session.add(deployment)
        else:
            deployment.status = status
            deployment.rolled_back_at = _parse_dt(raw.get("rolled_back_at"))

        if status == DeploymentStatus.ACTIVE:
            active_deployment = deployment

    await session.flush()

    if active_deployment is not None:
        service.active_deployment_id = active_deployment.id

    return active_deployment
