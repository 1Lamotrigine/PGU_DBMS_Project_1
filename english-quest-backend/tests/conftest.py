import os
import tempfile

# Configure an isolated database BEFORE importing the app.
_DB_PATH = os.path.join(tempfile.gettempdir(), "english_quest_test.db")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///" + _DB_PATH
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-1234"
os.environ["APP_ENV"] = "development"
os.environ["RATE_LIMIT_ENABLED"] = "false"
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from src.app import app  # noqa: E402
from src.config.database import AsyncSessionLocal, Base, engine  # noqa: E402
from src.db.seed import seed  # noqa: E402
from src.models import models  # noqa: E402,F401


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed(session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session():
    async with AsyncSessionLocal() as s:
        yield s
