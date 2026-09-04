from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.services.demo_reset import reset_demo_service
from app.services.service_registry import get_or_create_service
from app.services.simulator_client import get_simulator_client
from app.services.telemetry import DEMO_SERVICE_NAME

router = APIRouter(prefix="/simulator", tags=["simulator"])
logger = get_logger(__name__)


@router.post("/deployments/bad")
async def trigger_bad_deployment(request: Request) -> dict:
    client = get_simulator_client()
    deployment = await client.trigger_bad_deployment()
    logger.info("bad_deployment_triggered", version=deployment.get("version"))

    poller = getattr(request.app.state, "telemetry_poller", None)
    if poller is not None:
        await poller.poll_once()

    return deployment


@router.post("/reset")
async def reset_simulator(request: Request) -> dict:
    client = get_simulator_client()
    await client.reset()

    session: AsyncSession
    async with AsyncSessionLocal() as session:
        service = await get_or_create_service(session, DEMO_SERVICE_NAME)
        await reset_demo_service(session, service)
        await session.commit()

    poller = getattr(request.app.state, "telemetry_poller", None)
    if poller is not None:
        poller.reset_cursors()
        await poller.poll_once()

    logger.info("simulator_reset")
    return {"status": "reset"}
