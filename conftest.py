"""Pytest fixtures for Artisa backend tests."""

import asyncio
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from core.database import db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    """Initialize MongoDB connection for tests."""
    await db.connect_db()
    yield


@pytest.fixture
async def async_client():
    """Async HTTP Client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
