import asyncio
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from app.core.config import get_settings
from app.main import app

API_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def client():
    # Used as a context manager (not just `TestClient(app)`) so it opens
    # ONE persistent event loop/portal for every request made through it
    # for the whole session — see the super_admin_credentials fixture
    # docstring. Without `with`, Starlette's TestClient spins up a brand
    # new event loop per request, which breaks the app's cached
    # AsyncSessionLocal/get_redis() connections on the second call.
    with TestClient(app) as test_client:
        yield test_client


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def unique_mobile() -> str:
    # Valid-looking BD mobile: 01<3-9><8 digits>
    return "017" + str(uuid.uuid4().int)[:8]


def _create_admin_user(role: str) -> dict[str, str]:
    """Bootstraps a real admin user via the CLI script, run as a
    subprocess (its own process/engine/event loop) rather than importing
    app.core.database directly here — see docs/Implementation Plan.md
    Phase 1 notes on avoiding cross-event-loop asyncpg connection reuse
    between test setup and the app's own TestClient-driven event loop.
    """
    email = unique_email(role)
    password = "SuperSecret123"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.create_admin_user",
            "--email",
            email,
            "--password",
            password,
            "--role",
            role,
        ],
        cwd=API_ROOT,
        check=True,
        capture_output=True,
    )
    return {"email": email, "password": password}


@pytest.fixture(scope="session")
def super_admin_credentials() -> dict[str, str]:
    return _create_admin_user("super_admin")


@pytest.fixture(scope="session")
def customer_support_credentials() -> dict[str, str]:
    return _create_admin_user("customer_support")


async def _flush_rate_limit_keys() -> None:
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        keys = await redis.keys("rate_limit:*")
        if keys:
            await redis.delete(*keys)
    finally:
        await redis.aclose()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Each test starts with a clean rate-limit slate, using a throwaway
    Redis client/event loop independent of the app's own — see the
    super_admin_credentials fixture docstring for why that separation
    matters here too."""
    asyncio.run(_flush_rate_limit_keys())
    yield
