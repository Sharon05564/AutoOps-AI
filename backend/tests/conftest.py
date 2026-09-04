from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models.service import Service
from app.services import remediation_service

TABLES = [
    "verifications",
    "postmortems",
    "approvals",
    "remediation_actions",
    "agent_tool_calls",
    "investigations",
    "alerts",
    "incidents",
    "log_entries",
    "metric_snapshots",
    "deployments",
    "services",
]


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    """Truncate every table before each test so tests don't see each other's data.

    Requires a real Postgres reachable at DATABASE_URL (defaults to the
    docker-compose postgres service on localhost:5432) - the async UUID/JSON
    column types used throughout the models aren't SQLite-compatible.

    Disposes the engine's connection pool first: pytest-asyncio gives each
    test function its own fresh event loop, but the SQLAlchemy async engine
    is a single module-level object whose pooled connections are bound to
    whichever loop created them. Without disposing, a connection opened
    during a previous test's (now-closed) loop gets reused here and asyncpg
    raises "attached to a different loop".
    """
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
    yield


@pytest.fixture(autouse=True)
def _disable_automatic_verification(monkeypatch: pytest.MonkeyPatch):
    """Tests drive verification explicitly instead of waiting on the
    real 10s background timer, which would otherwise leave a dangling
    asyncio task at the end of every test that executes a remediation."""
    monkeypatch.setattr(
        remediation_service, "schedule_automatic_verification", lambda *a, **k: None
    )


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def service(db_session: AsyncSession) -> Service:
    svc = Service(name="checkout-service")
    db_session.add(svc)
    await db_session.commit()
    await db_session.refresh(svc)
    return svc


def now() -> datetime:
    return datetime.now(UTC)


def minutes_ago(n: float) -> datetime:
    return now() - timedelta(minutes=n)
