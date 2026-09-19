"""Phase 8 reliability pass: concurrency/race-condition coverage for
BR-INV ("inventory shall never go negative") under real concurrent
load, re-verifying Phase 5's transactional consistency now that
orders/service.py batches its FOR UPDATE locks (Phase 8 performance
pass) instead of taking them one row at a time.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from tests.conftest import unique_email
from tests.test_shipping import inline_address, setup_stocked_variant


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_customer(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email("race"), "password": "Passw0rd1", "full_name": "Race Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["access_token"]


def _place_order(client: TestClient, token: str, variant_id: str) -> dict:
    headers = auth_headers(token)
    add = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"product_variant_id": variant_id, "quantity": 1},
    )
    assert add.status_code == 201, add.text

    return client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
        },
    )


def test_concurrent_checkouts_never_oversell_last_unit(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
) -> None:
    """BR-INV: with exactly one unit of stock and five concurrent
    checkout attempts racing for it, exactly one must succeed and the
    rest must be rejected with INSUFFICIENT_STOCK — never more than one
    order placed against a single unit, and inventory must never go
    negative."""
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=1
    )

    concurrent_buyers = 5
    tokens = [_register_customer(client) for _ in range(concurrent_buyers)]

    with ThreadPoolExecutor(max_workers=concurrent_buyers) as pool:
        futures = [pool.submit(_place_order, client, token, variant["id"]) for token in tokens]
        responses = [f.result() for f in futures]

    successes = [r for r in responses if r.status_code == 201]
    failures = [r for r in responses if r.status_code == 422]

    assert len(successes) == 1, [r.text for r in responses]
    assert len(failures) == concurrent_buyers - 1
    assert all(r.json()["error"]["code"] == "INSUFFICIENT_STOCK" for r in failures)

    inv_headers = auth_headers(
        client.post("/api/v1/admin/auth/login", json=inventory_manager_credentials).json()["data"][
            "access_token"
        ]
    )
    # available is now 0 (<= the default reorder_threshold), so it's
    # guaranteed to show up in the low-stock filter regardless of how
    # many other variants earlier tests in this run have created.
    inventory = client.get(
        "/api/v1/admin/inventory", headers=inv_headers, params={"low_stock": True, "limit": 100}
    ).json()["data"]["items"]
    row = next(item for item in inventory if item["product_variant_id"] == variant["id"])
    assert row["quantity_on_hand"] == 1
    assert row["quantity_reserved"] == 1
    assert row["quantity_available"] == 0
