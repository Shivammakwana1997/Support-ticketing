"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from models.base import Base
from api.dependencies.database import get_db
from api.dependencies.auth import get_current_user
from core.config import settings


# ── Test database engine ──
TEST_DATABASE_URL = settings.DATABASE_URL.replace("copilot", "copilot_test") if "copilot_test" not in settings.DATABASE_URL else settings.DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ── Event loop ──
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── Database setup/teardown ──
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Override dependencies ──
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden dependencies."""

    async def override_get_db():
        yield db_session

    # Mock authenticated user
    mock_user = type("MockUser", (), {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "email": "test@example.com",
        "role": "admin",
        "display_name": "Test User",
        "is_active": True,
    })()

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac._mock_user = mock_user  # type: ignore
        yield ac

    app.dependency_overrides.clear()


# ── Helper fixtures ──
@pytest.fixture
def tenant_id() -> str:
    """Return a test tenant ID."""
    return str(uuid4())


@pytest.fixture
def customer_id() -> str:
    """Return a test customer ID."""
    return str(uuid4())
