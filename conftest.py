"""Pytest fixtures for Artisa backend tests."""

import sys
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from core.database import db


@pytest_asyncio.fixture(scope="session", autouse=False)
async def init_test_db():
    """Initialize MongoDB connection for integration tests."""
    await db.connect_db()
    yield


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP Client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
