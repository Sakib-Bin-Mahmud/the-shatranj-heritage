import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path

# Must run before `app.main` (and anything importing app.core.config) is
# ever imported below, since Settings is cached on first read: tests that
# exercise image upload need S3_ENDPOINT_URL pointed at the in-process
# moto server started by the `moto_s3_server` fixture, not the real
# MinIO instance docker-compose provides outside tests.
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9099")

# Same reasoning: payment tests must never reach the real SSLCommerz
# sandbox over the network. FakePaymentProvider still exercises real
# HMAC signature verification (see app/modules/payments/providers.py).
os.environ.setdefault("PAYMENT_PROVIDER", "fake")

import pytest
from fastapi.testclient import TestClient
from moto.server import ThreadedMotoServer
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


@pytest.fixture(scope="session")
def inventory_manager_credentials() -> dict[str, str]:
    return _create_admin_user("inventory_manager")


@pytest.fixture(scope="session")
def content_manager_credentials() -> dict[str, str]:
    return _create_admin_user("content_manager")


@pytest.fixture(scope="session")
def order_manager_credentials() -> dict[str, str]:
    return _create_admin_user("order_manager")


@pytest.fixture(scope="session", autouse=True)
def moto_s3_server():
    """An in-process fake S3 server backing app.core.storage in tests,
    so image-upload tests don't depend on a real MinIO instance (only
    docker-compose runs that, not CI or this test suite)."""
    server = ThreadedMotoServer(port=9099)
    server.start()
    yield
    server.stop()


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
