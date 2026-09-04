from fastapi import APIRouter

from app.api.routes import deployments, incidents, services, simulator

api_router = APIRouter(prefix="/api")
api_router.include_router(services.router)
api_router.include_router(incidents.router)
api_router.include_router(deployments.router)
api_router.include_router(simulator.router)
