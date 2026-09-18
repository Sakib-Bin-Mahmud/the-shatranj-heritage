import asyncio
import json
import uuid

import asyncpg
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.modules.notifications.providers import LoggingNotificationChannel
from tests.conftest import unique_email

# No dedicated notifications API exists (push-only service, see
# app/modules/notifications/router.py's removal note) — assertions read
# the `notifications_log` ledger via a throwaway asyncpg connection,
# mirroring conftest.py's `_flush_rate_limit_keys` pattern of using an
# independent connection/event loop rather than the app's own.


def _dsn() -> str:
    return get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://")


async def _fetch_notification_logs(*, template_code: str, recipient: str) -> list[dict]:
    conn = await asyncpg.connect(_dsn())
    try:
        rows = await conn.fetch(
            "SELECT * FROM notifications_log WHERE template_code = $1 AND recipient = $2",
            template_code,
            recipient,
        )
        # asyncpg returns JSONB columns as raw text without an explicit
        # codec, so decode `payload` back into a dict for callers.
        results = []
        for row in rows:
            record = dict(row)
            if isinstance(record.get("payload"), str):
                record["payload"] = json.loads(record["payload"])
            results.append(record)
        return results
    finally:
        await conn.close()


def fetch_notification_logs(*, template_code: str, recipient: str) -> list[dict]:
    return asyncio.run(_fetch_notification_logs(template_code=template_code, recipient=recipient))


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def test_registration_logs_welcome_notification(client: TestClient) -> None:
    email = unique_email("welcome")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd1", "full_name": "Welcome Test"},
    )
    assert response.status_code == 201, response.text

    logs = fetch_notification_logs(template_code="registration_welcome", recipient=email)
    assert len(logs) == 1
    assert logs[0]["status"] == "sent"
    assert logs[0]["channel"] == "email"


def test_password_reset_token_is_redacted_in_notification_log(client: TestClient) -> None:
    email = unique_email("reset")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd1", "full_name": "Reset Test"},
    )

    forgot = client.post("/api/v1/auth/forgot-password", json={"identifier": email})
    assert forgot.status_code == 200
    raw_token = forgot.json()["data"]["debug_reset_token"]

    logs = fetch_notification_logs(template_code="password_reset", recipient=email)
    assert len(logs) == 1
    payload = logs[0]["payload"]
    # The real token was used to actually send (proven by the API's own
    # debug echo working against it in test_auth.py); only the persisted
    # ledger copy is masked.
    assert payload["reset_token"] == "[REDACTED]"
    assert raw_token != "[REDACTED]"


def test_notification_send_failure_does_not_block_registration(
    client: TestClient, monkeypatch
) -> None:
    """NFR-AVL-003: a broken notification channel must never block the
    business operation that triggered it."""

    async def boom(self, *, recipient, subject, body):
        raise RuntimeError("simulated channel outage")

    monkeypatch.setattr(LoggingNotificationChannel, "send_email", boom)

    email = unique_email("notif-fail")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd1", "full_name": "Notif Fail"},
    )
    assert response.status_code == 201, response.text

    logs = fetch_notification_logs(template_code="registration_welcome", recipient=email)
    assert len(logs) == 1
    assert logs[0]["status"] == "failed"


def test_order_confirmation_notification_logged(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
) -> None:
    client.cookies.clear()
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))

    suffix = uuid.uuid4().hex[:8]
    category = client.post(
        "/api/v1/admin/categories",
        headers=content_headers,
        json={"name": f"Category {suffix}", "slug": f"category-{suffix}"},
    ).json()["data"]
    product = client.post(
        "/api/v1/admin/products",
        headers=inv_headers,
        json={
            "sku": f"SKU-{suffix}",
            "name": f"Product {suffix}",
            "slug": f"product-{suffix}",
            "category_id": category["id"],
            "base_price": "1000.00",
            "status": "active",
        },
    ).json()["data"]
    variant_resp = client.post(
        f"/api/v1/admin/products/{product['id']}/variants",
        headers=inv_headers,
        json={"sku": f"VAR-{suffix}", "variant_name": "Standard"},
    ).json()["data"]
    variant = variant_resp["variants"][-1]
    client.patch(
        f"/api/v1/admin/inventory/{variant['id']}/adjust",
        headers=inv_headers,
        json={"change_type": "restock", "quantity_delta": 5, "note": "test restock"},
    )

    email = unique_email("order-confirm")
    client.post("/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1})
    client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": {
                "recipient_name": "Karim Ahmed",
                "phone": "01711111111",
                "address_line1": "House 12, Road 5",
                "city": "Dhaka",
                "district": "Dhaka",
                "country": "BD",
            },
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": email,
        },
    )

    logs = fetch_notification_logs(template_code="order_confirmation", recipient=email)
    assert len(logs) == 1
    assert logs[0]["status"] == "sent"
