import uuid

from fastapi.testclient import TestClient

from tests.conftest import unique_email

# --- Shared helpers (mirrors tests/test_orders.py's conventions) --------


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


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


def place_packed_order(
    client: TestClient, *, variant_id: str, customer_headers: dict, order_headers: dict
) -> dict:
    """Places a COD order for the given variant and drives it to
    'packed' via the admin lifecycle, returning the admin order detail."""
    add_to_cart(client, variant_id, 1, headers=customer_headers)
    payload = {"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"}
    if not customer_headers:
        payload["guest_email"] = unique_email()

    placed = client.post(
        "/api/v1/orders",
        headers={**customer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json=payload,
    ).json()["data"]

    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    order_id = next(
        o["id"] for o in admin_orders if o["order_number"] == placed["order"]["order_number"]
    )
    for status in ("confirmed", "packed"):
        r = client.patch(
            f"/api/v1/admin/orders/{order_id}/status",
            headers=order_headers,
            json={"status": status},
        )
        assert r.status_code == 200, r.text

    return client.get(f"/api/v1/admin/orders/{order_id}", headers=order_headers).json()["data"]


# --- Shipping cost calculation (US-SHP-001, BR-SHP-002) -------------------


def test_shipping_cost_higher_outside_dhaka(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add_to_cart(client, variant["id"], 1)

    dhaka = client.post(
        "/api/v1/checkout/quote",
        json={"address": inline_address(district="Dhaka"), "shipping_method": "standard"},
    ).json()["data"]
    outside = client.post(
        "/api/v1/checkout/quote",
        json={"address": inline_address(district="Chittagong"), "shipping_method": "standard"},
    ).json()["data"]

    assert dhaka["shipping_amount"] == "60.00"
    assert outside["shipping_amount"] == "100.00"


def test_shipping_cost_increases_with_weight(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, weight_grams=2500
    )
    add_to_cart(client, variant["id"], 1)

    quote = client.post(
        "/api/v1/checkout/quote",
        json={"address": inline_address(district="Dhaka"), "shipping_method": "standard"},
    ).json()["data"]

    # base 1000g covered by base_rate (60.00); 1500g extra rounds up to
    # 2kg at 15.00/kg = 30.00 -> 90.00 total.
    assert quote["shipping_amount"] == "90.00"


# --- Courier assignment (US-SHP-002) --------------------------------------


def test_assign_courier_requires_packed_order(
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

    # Order is only 'awaiting_payment' — not yet packed.
    response = client.post(
        f"/api/v1/admin/orders/{order_id}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ORDER_STATE"


def test_assign_courier_ships_order_and_uses_manual_tracking_number(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    order_detail = place_packed_order(
        client, variant_id=variant["id"], customer_headers={}, order_headers=order_headers
    )
    assert order_detail["status"] == "packed"

    response = client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao", "tracking_number": "PATHAO-MANUAL-123"},
    )
    assert response.status_code == 201, response.text
    shipment = response.json()["data"]
    assert shipment["tracking_number"] == "PATHAO-MANUAL-123"
    assert shipment["status"] == "pending"

    order_after = client.get(
        f"/api/v1/admin/orders/{order_detail['id']}", headers=order_headers
    ).json()["data"]
    assert order_after["status"] == "shipped"


def test_admin_can_read_back_an_assigned_shipment(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    """Every other shipment endpoint only returns one as the side
    effect of changing it — this is the only way to see an order's
    current shipment on a fresh page load."""
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    order_detail = place_packed_order(
        client, variant_id=variant["id"], customer_headers={}, order_headers=order_headers
    )

    client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao", "tracking_number": "PATHAO-READBACK-1"},
    )

    response = client.get(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment", headers=order_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["tracking_number"] == "PATHAO-READBACK-1"


def test_admin_get_shipment_404s_before_assignment(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    order_detail = place_packed_order(
        client, variant_id=variant["id"], customer_headers={}, order_headers=order_headers
    )

    response = client.get(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment", headers=order_headers
    )
    assert response.status_code == 404


def test_non_order_manager_cannot_read_shipment(client: TestClient, customer_support_credentials):
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get(f"/api/v1/admin/orders/{uuid.uuid4()}/shipment", headers=headers)
    assert response.status_code == 403


def test_assign_courier_without_tracking_number_uses_provider(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    order_detail = place_packed_order(
        client, variant_id=variant["id"], customer_headers={}, order_headers=order_headers
    )

    response = client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao"},
    )
    assert response.status_code == 201, response.text
    shipment = response.json()["data"]
    assert shipment["tracking_number"].startswith("FAKE-TRACK-")
    assert shipment["estimated_delivery_date"] is not None


def test_cannot_assign_second_shipment_to_same_order(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_headers = auth_headers(admin_token(client, order_manager_credentials))
    order_detail = place_packed_order(
        client, variant_id=variant["id"], customer_headers={}, order_headers=order_headers
    )
    client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao", "tracking_number": "TRACK-1"},
    )

    # The first assignment already moved the order to 'shipped', so a
    # second attempt is rejected by the order-state gate before it can
    # even reach shipping/service.py's own duplicate-shipment check.
    duplicate = client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "RedX", "tracking_number": "TRACK-2"},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "INVALID_ORDER_STATE"


def test_non_order_manager_cannot_assign_shipment(client: TestClient, customer_support_credentials):
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.post(
        f"/api/v1/admin/orders/{uuid.uuid4()}/shipment",
        headers=headers,
        json={"courier_name": "Pathao"},
    )
    assert response.status_code == 403


# --- Tracking + delivery confirmation (US-SHP-003/004) --------------------


def test_customer_cannot_view_shipment_before_assignment(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    register = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "Passw0rd1", "full_name": "Tracker"},
    ).json()["data"]
    headers = auth_headers(register["access_token"])
    add_to_cart(client, variant["id"], 1, headers=headers)
    placed = client.post(
        "/api/v1/orders",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"address": inline_address(), "shipping_method": "standard", "payment_method": "cod"},
    ).json()["data"]

    response = client.get(
        f"/api/v1/orders/{placed['order']['order_number']}/shipment", headers=headers
    )
    assert response.status_code == 404


def test_full_shipment_lifecycle_to_delivered(
    client: TestClient,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    register = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "Passw0rd1", "full_name": "Tracker"},
    ).json()["data"]
    customer_headers = auth_headers(register["access_token"])
    order_headers = auth_headers(admin_token(client, order_manager_credentials))

    order_detail = place_packed_order(
        client,
        variant_id=variant["id"],
        customer_headers=customer_headers,
        order_headers=order_headers,
    )
    shipment = client.post(
        f"/api/v1/admin/orders/{order_detail['id']}/shipment",
        headers=order_headers,
        json={"courier_name": "Pathao", "tracking_number": "TRACK-LIFECYCLE"},
    ).json()["data"]

    # Customer can now see tracking info.
    tracking = client.get(
        f"/api/v1/orders/{order_detail['order_number']}/shipment", headers=customer_headers
    ).json()["data"]
    assert tracking["tracking_number"] == "TRACK-LIFECYCLE"
    assert tracking["status"] == "pending"

    # Skipping straight to delivered is rejected.
    skip = client.patch(
        f"/api/v1/admin/shipments/{shipment['id']}/status",
        headers=order_headers,
        json={"status": "delivered"},
    )
    assert skip.status_code == 422
    assert skip.json()["error"]["code"] == "INVALID_TRANSITION"

    for status in ("dispatched", "in_transit", "delivered"):
        r = client.patch(
            f"/api/v1/admin/shipments/{shipment['id']}/status",
            headers=order_headers,
            json={"status": status},
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status"] == status

    final_order = client.get(
        f"/api/v1/admin/orders/{order_detail['id']}", headers=order_headers
    ).json()["data"]
    assert final_order["status"] == "delivered"

    final_tracking = client.get(
        f"/api/v1/orders/{order_detail['order_number']}/shipment", headers=customer_headers
    ).json()["data"]
    assert final_tracking["status"] == "delivered"
    assert final_tracking["delivered_at"] is not None
