import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentRead

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentRead])
async def list_deployments(
    service_id: uuid.UUID | None = None, session: AsyncSession = Depends(get_db)
) -> list[DeploymentRead]:
    query = select(Deployment).order_by(Deployment.deployed_at.desc())
    if service_id is not None:
        query = query.where(Deployment.service_id == service_id)
    result = await session.execute(query)
    return [DeploymentRead.model_validate(d) for d in result.scalars().all()]
