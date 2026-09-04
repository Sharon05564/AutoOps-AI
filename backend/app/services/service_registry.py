from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service


async def get_or_create_service(session: AsyncSession, name: str) -> Service:
    result = await session.execute(select(Service).where(Service.name == name))
    service = result.scalar_one_or_none()
    if service is not None:
        return service

    service = Service(name=name)
    session.add(service)
    await session.flush()
    return service
