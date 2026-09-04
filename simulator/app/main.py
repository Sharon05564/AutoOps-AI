import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.config import get_simulator_settings
from app.schemas import DeploymentInfo, LogLine, MetricPoint, ScaleRequest, ServiceState
from app.state import SimulatorState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulator")

settings = get_simulator_settings()
state = SimulatorState(settings=settings)


async def _tick_loop() -> None:
    while True:
        try:
            state.tick()
        except Exception:  # pragma: no cover - defensive, keeps the loop alive
            logger.exception("simulator tick failed")
        await asyncio.sleep(settings.tick_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_tick_loop())
    logger.info("simulator started for service=%s", settings.service_name)
    yield
    task.cancel()


app = FastAPI(title="AutoOps Simulator", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/internal/state", response_model=ServiceState)
async def get_state() -> ServiceState:
    return state.get_state()


@app.get("/internal/metrics", response_model=list[MetricPoint])
async def get_recent_metrics(window_seconds: int = 60) -> list[MetricPoint]:
    return state.get_recent_metrics(window_seconds)


@app.get("/internal/logs", response_model=list[LogLine])
async def get_recent_logs(window_seconds: int = 60, limit: int = 200) -> list[LogLine]:
    return state.get_recent_logs(window_seconds, limit)


@app.get("/internal/deployments", response_model=list[DeploymentInfo])
async def get_deployments() -> list[DeploymentInfo]:
    return state.get_deployments()


@app.post("/deployments/bad", response_model=DeploymentInfo)
async def trigger_bad_deployment() -> DeploymentInfo:
    deployment = state.trigger_bad_deployment()
    return deployment.to_schema()


@app.post("/deployments/rollback", response_model=DeploymentInfo | None)
async def rollback_deployment() -> DeploymentInfo | None:
    previous = state.rollback()
    return previous.to_schema() if previous else None


@app.post("/restart")
async def restart_service() -> dict[str, str]:
    state.restart()
    return {"status": "restarted"}


@app.post("/scale")
async def scale_service(request: ScaleRequest) -> dict[str, int]:
    try:
        state.scale(request.replicas)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"replicas": state.replicas}


@app.post("/reset")
async def reset_simulator() -> dict[str, str]:
    state.reset()
    return {"status": "reset"}
