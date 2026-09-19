import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.modules.inventory.service import refresh_low_stock_gauge
from tests.conftest import unique_email
from tests.test_shipping import add_to_cart, inline_address, setup_stocked_variant


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def test_metrics_endpoint_exposes_prometheus_format(client: TestClient) -> None:
    """NFR-MON-001."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Request-level metrics from prometheus-fastapi-instrumentator.
    assert "http_requests_total" in response.text


def test_order_placement_increments_orders_placed_counter(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
) -> None:
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)
    placed = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
    )
    assert placed.status_code == 201, placed.text

    metrics = client.get("/metrics").text
    assert 'orders_placed_total{payment_method="cod"}' in metrics


def test_low_stock_gauge_reflects_low_stock_variant(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
) -> None:
    """NFR-MON-002 (alerting for low stock): the gauge is normally kept
    fresh by main.py's background loop; the test calls the same
    refresh function directly rather than waiting on the interval."""
    setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=1
    )

    async def _refresh() -> int:
        # A throwaway engine, scoped entirely within this asyncio.run()
        # call, rather than the app's own AsyncSessionLocal — that
        # engine's asyncpg connections are bound to the TestClient's
        # persistent event loop (see conftest.py's super_admin_credentials
        # docstring), and reusing them from a fresh loop here breaks them.
        engine = create_async_engine(get_settings().database_url)
        try:
            session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
            async with session_factory() as session:
                return await refresh_low_stock_gauge(session)
        finally:
            await engine.dispose()

    count = asyncio.run(_refresh())
    assert count >= 1

    metrics = client.get("/metrics").text
    assert "low_stock_variants" in metrics
    assert f"low_stock_variants {float(count)}" in metrics
