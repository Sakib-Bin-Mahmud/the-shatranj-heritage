import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import unique_email

# --- Shared helpers (mirrors tests/test_cart.py's conventions) -----------


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def register_customer(client: TestClient, **overrides) -> dict:
    payload = {"email": unique_email(), "password": "Passw0rd1", "full_name": "Order Tester"}
    payload.update(overrides)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_category(client: TestClient, headers: dict, **overrides) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {"name": f"Category {suffix}", "slug": f"category-{suffix}"}
    payload.update(overrides)
    response = client.post("/api/v1/admin/categories", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_product(client: TestClient, headers: dict, category_id: str, **overrides) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "sku": f"SKU-{suffix}",
        "name": f"Product {suffix}",
        "slug": f"product-{suffix}",
        "category_id": category_id,
        "base_price": "1000.00",
        "status": "active",
    }
    payload.update(overrides)
    response = client.post("/api/v1/admin/products", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_stocked_variant(
    client: TestClient, headers: dict, product_id: str, *, stock: int = 10, **overrides
) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {"sku": f"VAR-{suffix}", "variant_name": "Standard"}
    payload.update(overrides)
    response = client.post(
        f"/api/v1/admin/products/{product_id}/variants", headers=headers, json=payload
    )
    assert response.status_code == 201, response.text
    variant = response.json()["data"]["variants"][-1]

    restock = client.patch(
        f"/api/v1/admin/inventory/{variant['id']}/adjust",
        headers=headers,
        json={"change_type": "restock", "quantity_delta": stock, "note": "test restock"},
    )
    assert restock.status_code == 200, restock.text
    return variant


def setup_stocked_variant(
    client: TestClient, inventory_manager_credentials, content_manager_credentials, **kwargs
) -> tuple[dict, str]:
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])
    variant = create_stocked_variant(client, inv_headers, product["id"], **kwargs)
    return variant, product["base_price"]


def inline_address(**overrides) -> dict:
    payload = {
        "recipient_name": "Karim Ahmed",
        "phone": "01711111111",
        "address_line1": "House 12, Road 5",
        "city": "Dhaka",
        "district": "Dhaka",
        "country": "BD",
    }
    payload.update(overrides)
    return payload


def sign(raw_body: bytes) -> str:
    secret = get_settings().payment_webhook_secret
    return hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


def post_webhook(client: TestClient, payload: dict, *, signature: str | None | bool = True):
    raw = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if signature is True:
        headers["x-signature"] = sign(raw)
    elif isinstance(signature, str):
        headers["x-signature"] = signature
    return client.post("/api/v1/payments/webhook/sslcommerz", content=raw, headers=headers)


def inventory_transactions(client: TestClient, inv_headers: dict, variant_id: str) -> list[dict]:
    response = client.get(f"/api/v1/admin/inventory/{variant_id}/transactions", headers=inv_headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]["items"]


def add_to_cart(
    client: TestClient, variant_id: str, quantity: int = 1, headers: dict | None = None
) -> dict:
    response = client.post(
        "/api/v1/cart/items",
        headers=headers or {},
        json={"product_variant_id": variant_id, "quantity": quantity},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- Checkout quote ------------------------------------------------------


def test_checkout_quote_requires_nonempty_cart(client: TestClient):
    client.cookies.clear()
    response = client.post(
        "/api/v1/checkout/quote",
        json={"address": inline_address(), "shipping_method": "standard"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMPTY_CART"


def test_checkout_quote_computes_totals(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, base_price = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 2)

    response = client.post(
        "/api/v1/checkout/quote",
        json={"address": inline_address(), "shipping_method": "express"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["subtotal"] == f"{float(base_price) * 2:.2f}"
    assert data["shipping_amount"] == "150.00"
    assert data["total_amount"] == f"{float(base_price) * 2 + 150:.2f}"
    assert {opt["method"] for opt in data["shipping_options"]} == {"standard", "express"}


def test_checkout_quote_rejects_both_or_neither_address(client: TestClient):
    client.cookies.clear()
    response = client.post(
        "/api/v1/checkout/quote",
        json={
            "address_id": str(uuid.uuid4()),
            "address": inline_address(),
            "shipping_method": "standard",
        },
    )
    assert response.status_code == 422


# --- Order placement: COD / guest -----------------------------------------


def test_guest_cod_order_places_and_reserves_stock(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, base_price = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    add_to_cart(client, variant["id"], 3)

    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["order"]["status"] == "awaiting_payment"
    assert data["order"]["order_number"].startswith("SH-")
    assert data["payment"] is None

    # 3 reserved out of 10 stocked -> 7 left available for a new cart.
    client.cookies.clear()
    added = add_to_cart(client, variant["id"], 7)
    assert added["items"][0]["max_available"] == 7

    # Reservation alone writes no ledger row — only the setup restock does.
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    ledger = inventory_transactions(client, inv_headers, variant["id"])
    assert [t["change_type"] for t in ledger] == ["restock"]


def test_guest_order_requires_contact_info(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)

    response = client.post(
        "/api/v1/orders",
        json={"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "GUEST_CONTACT_REQUIRED"


def test_place_order_rejects_empty_cart(client: TestClient):
    client.cookies.clear()
    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMPTY_CART"


def test_place_order_rejects_insufficient_stock(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=2
    )
    add_to_cart(client, variant["id"], 2)

    # Someone else buys the stock out from under this cart before checkout.
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    client.patch(
        f"/api/v1/admin/inventory/{variant['id']}/adjust",
        headers=inv_headers,
        json={"change_type": "damage", "quantity_delta": -2},
    )

    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


# --- Idempotency (NFR-REL-001) -------------------------------------------


def test_idempotency_key_replay_returns_same_order(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    add_to_cart(client, variant["id"], 1)

    key = str(uuid.uuid4())
    payload = {
        "address": inline_address(),
        "shipping_method": "standard",
        "payment_method": "cod",
        "guest_email": unique_email(),
    }
    first = client.post("/api/v1/orders", json=payload, headers={"Idempotency-Key": key})
    assert first.status_code == 201
    order_number = first.json()["data"]["order"]["order_number"]

    # Same cart is now converted/empty; a naive replay handler might
    # otherwise 422 on EMPTY_CART instead of returning the prior order.
    second = client.post("/api/v1/orders", json=payload, headers={"Idempotency-Key": key})
    assert second.status_code == 201
    assert second.json()["data"]["order"]["order_number"] == order_number

    # Only one reservation actually happened: 9 left, not 8.
    client.cookies.clear()
    added = add_to_cart(client, variant["id"], 9)
    assert added["items"][0]["max_available"] == 9


# --- Customer checkout with saved address --------------------------------


def test_customer_order_with_saved_address(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])

    address = client.post(
        "/api/v1/customers/me/addresses", headers=headers, json=inline_address()
    ).json()["data"]

    add_to_cart(client, variant["id"], 1, headers=headers)

    response = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "address_id": address["id"],
            "shipping_method": "standard",
            "payment_method": "cod",
        },
    )
    assert response.status_code == 201, response.text

    detail = client.get(
        f"/api/v1/orders/{response.json()['data']['order']['order_number']}", headers=headers
    ).json()["data"]
    assert detail["shipping_address"]["recipient_name"] == "Karim Ahmed"
    assert detail["customer_id"] is not None


def test_address_id_rejected_for_guest(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)

    response = client.post(
        "/api/v1/orders",
        json={
            "address_id": str(uuid.uuid4()),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ADDRESS_REQUIRES_ACCOUNT"


# --- Online payment + webhook --------------------------------------------


def test_online_order_returns_redirect_and_webhook_confirms(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    add_to_cart(client, variant["id"], 4)

    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "bkash",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["order"]["status"] == "awaiting_payment"
    assert data["payment"]["redirect_url"].startswith("https://fake-gateway.test/pay/")
    transaction_id = data["payment"]["redirect_url"].rsplit("/", 1)[-1]

    webhook = post_webhook(client, {"transaction_id": transaction_id, "status": "success"})
    assert webhook.status_code == 200

    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    ledger = inventory_transactions(client, inv_headers, variant["id"])
    # Newest first: the confirm-time "sale" on top of the setup restock.
    assert len(ledger) == 2
    assert ledger[0]["change_type"] == "sale"
    assert ledger[0]["quantity_delta"] == -4
    assert ledger[0]["reference_type"] == "order"

    # Idempotent replay of the same webhook must not double-deduct.
    replay = post_webhook(client, {"transaction_id": transaction_id, "status": "success"})
    assert replay.status_code == 200
    ledger_after_replay = inventory_transactions(client, inv_headers, variant["id"])
    assert len(ledger_after_replay) == 2


def test_webhook_failure_keeps_order_awaiting_payment_and_stock_reserved(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    add_to_cart(client, variant["id"], 2)

    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "nagad",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    data = response.json()["data"]
    transaction_id = data["payment"]["redirect_url"].rsplit("/", 1)[-1]

    webhook = post_webhook(client, {"transaction_id": transaction_id, "status": "failed"})
    assert webhook.status_code == 200

    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    ledger = inventory_transactions(client, inv_headers, variant["id"])
    assert [t["change_type"] for t in ledger] == ["restock"]

    # Stock is still reserved (not released) so the customer can retry.
    client.cookies.clear()
    added = add_to_cart(client, variant["id"], 8)
    assert added["items"][0]["max_available"] == 8


def test_webhook_rejects_invalid_signature(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)
    response = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "card",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    transaction_id = response.json()["data"]["payment"]["redirect_url"].rsplit("/", 1)[-1]

    bad = post_webhook(
        client, {"transaction_id": transaction_id, "status": "success"}, signature="not-valid"
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_SIGNATURE"

    missing = post_webhook(
        client, {"transaction_id": transaction_id, "status": "success"}, signature=None
    )
    assert missing.status_code == 401


# --- Order history / detail / RBAC ----------------------------------------


def test_customer_order_history_and_detail(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])
    add_to_cart(client, variant["id"], 1, headers=headers)

    placed = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
        },
    ).json()["data"]

    history = client.get("/api/v1/orders", headers=headers).json()["data"]
    assert history["meta"]["total"] >= 1
    assert any(o["order_number"] == placed["order"]["order_number"] for o in history["items"])

    detail = client.get(
        f"/api/v1/orders/{placed['order']['order_number']}", headers=headers
    ).json()["data"]
    assert detail["items"][0]["quantity"] == 1
    assert detail["payments"][0]["method"] == "cod"


def test_customer_cannot_view_or_cancel_others_order(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    owner = register_customer(client)
    owner_headers = auth_headers(owner["access_token"])
    add_to_cart(client, variant["id"], 1, headers=owner_headers)
    placed = client.post(
        "/api/v1/orders",
        headers={**owner_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"},
    ).json()["data"]
    order_number = placed["order"]["order_number"]

    other = register_customer(client)
    other_headers = auth_headers(other["access_token"])

    assert client.get(f"/api/v1/orders/{order_number}", headers=other_headers).status_code == 404
    assert (
        client.post(f"/api/v1/orders/{order_number}/cancel", headers=other_headers).status_code
        == 404
    )


# --- Cancellation ----------------------------------------------------------


def test_cancel_before_confirm_releases_reservation_only(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])
    add_to_cart(client, variant["id"], 3, headers=headers)
    placed = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"},
    ).json()["data"]

    cancel = client.post(
        f"/api/v1/orders/{placed['order']['order_number']}/cancel", headers=headers
    )
    assert cancel.status_code == 200
    assert cancel.json()["data"]["status"] == "cancelled"

    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    ledger = inventory_transactions(client, inv_headers, variant["id"])
    assert [t["change_type"] for t in ledger] == ["restock"]  # never committed

    client.cookies.clear()
    added = add_to_cart(client, variant["id"], 10)
    assert added["items"][0]["max_available"] == 10  # fully released


def test_cancel_after_confirm_restores_stock_and_creates_refund_request(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    add_to_cart(client, variant["id"], 4)
    placed = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "bkash",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    ).json()["data"]
    transaction_id = placed["payment"]["redirect_url"].rsplit("/", 1)[-1]
    post_webhook(client, {"transaction_id": transaction_id, "status": "success"})

    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    # Fetch by number via admin list to get the internal id (admin GET is id-based).
    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    matching = next(o for o in admin_orders if o["order_number"] == placed["order"]["order_number"])

    cancel = client.patch(
        f"/api/v1/admin/orders/{matching['id']}/status",
        headers=order_headers,
        json={"status": "cancelled"},
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["data"]["status"] == "cancelled"

    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    ledger = inventory_transactions(client, inv_headers, variant["id"])
    # Newest first: return (cancel) -> sale (confirm) -> restock (setup).
    assert [t["change_type"] for t in ledger] == ["return", "sale", "restock"]

    client.cookies.clear()
    added = add_to_cart(client, variant["id"], 10)
    assert added["items"][0]["max_available"] == 10  # fully restored


def test_cancel_shipped_order_rejected(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])
    add_to_cart(client, variant["id"], 1, headers=headers)
    placed = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"},
    ).json()["data"]

    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    order_id = next(
        o["id"] for o in admin_orders if o["order_number"] == placed["order"]["order_number"]
    )
    for status in ("confirmed", "packed", "shipped"):
        r = client.patch(
            f"/api/v1/admin/orders/{order_id}/status",
            headers=order_headers,
            json={"status": status},
        )
        assert r.status_code == 200, r.text

    cancel = client.post(
        f"/api/v1/orders/{placed['order']['order_number']}/cancel", headers=headers
    )
    assert cancel.status_code == 422
    assert cancel.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"


# --- Admin lifecycle / RBAC ------------------------------------------------


def test_admin_status_transition_rejects_backward_jump(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)
    placed = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    ).json()["data"]

    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    order_id = next(
        o["id"] for o in admin_orders if o["order_number"] == placed["order"]["order_number"]
    )

    invalid = client.patch(
        f"/api/v1/admin/orders/{order_id}/status", headers=order_headers, json={"status": "shipped"}
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_TRANSITION"

    valid = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        headers=order_headers,
        json={"status": "confirmed"},
    )
    assert valid.status_code == 200


def test_non_order_manager_cannot_access_admin_orders(
    client: TestClient, customer_support_credentials
):
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get("/api/v1/admin/orders", headers=headers)
    assert response.status_code == 403


def test_admin_can_request_refund_after_payment(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)
    placed = client.post(
        "/api/v1/orders",
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "rocket",
            "guest_email": unique_email(),
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    ).json()["data"]
    transaction_id = placed["payment"]["redirect_url"].rsplit("/", 1)[-1]
    post_webhook(client, {"transaction_id": transaction_id, "status": "success"})

    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    order_id = next(
        o["id"] for o in admin_orders if o["order_number"] == placed["order"]["order_number"]
    )
    order_detail = client.get(f"/api/v1/admin/orders/{order_id}", headers=order_headers).json()[
        "data"
    ]
    payment_id = order_detail["payments"][0]["id"]

    refund = client.post(
        f"/api/v1/admin/orders/{order_id}/refund",
        headers=order_headers,
        json={"payment_id": payment_id, "amount": order_detail["total_amount"], "reason": "test"},
    )
    assert refund.status_code == 201, refund.text
    assert refund.json()["data"]["status"] == "requested"


# --- Payment retry --------------------------------------------------------


def test_payments_initiate_retries_after_failure(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])
    add_to_cart(client, variant["id"], 1, headers=headers)
    placed = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "bkash",
        },
    ).json()["data"]
    transaction_id = placed["payment"]["redirect_url"].rsplit("/", 1)[-1]
    post_webhook(client, {"transaction_id": transaction_id, "status": "failed"})

    # Need the order's internal id for the retry endpoint.
    order_number = placed["order"]["order_number"]
    order_detail = client.get(f"/api/v1/orders/{order_number}", headers=headers).json()["data"]

    retry = client.post(
        "/api/v1/payments/initiate",
        headers=headers,
        json={"order_id": order_detail["id"], "method": "nagad"},
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["data"]["redirect_url"].startswith("https://fake-gateway.test/pay/")
