import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from tests.conftest import unique_email
from tests.test_orders import post_webhook
from tests.test_shipping import add_to_cart, inline_address, setup_stocked_variant


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def _place_and_confirm_cod_order(
    client: TestClient,
    *,
    variant_id: str,
    order_headers: dict,
) -> dict:
    """Places a guest COD order and drives it to 'confirmed', so it
    counts toward revenue (REVENUE_ORDER_STATUSES)."""
    add_to_cart(client, variant_id, 1)
    placed = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={
            "address": inline_address(),
            "shipping_method": "standard",
            "payment_method": "cod",
            "guest_email": unique_email(),
        },
    ).json()["data"]

    admin_orders = client.get("/api/v1/admin/orders", headers=order_headers).json()["data"]["items"]
    order_id = next(
        o["id"] for o in admin_orders if o["order_number"] == placed["order"]["order_number"]
    )
    confirm = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        headers=order_headers,
        json={"status": "confirmed"},
    )
    assert confirm.status_code == 200, confirm.text
    return client.get(f"/api/v1/admin/orders/{order_id}", headers=order_headers).json()["data"]


# --- Permission gate (reports.read) ----------------------------------------


def test_reports_require_permission(client: TestClient, customer_support_credentials) -> None:
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get("/api/v1/admin/reports/sales", headers=headers)
    assert response.status_code == 403


# --- Sales / revenue (US-RPT-001, FR-RPT-002) -------------------------------


def test_sales_report_counts_confirmed_order_as_revenue(
    client: TestClient,
    super_admin_credentials,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
) -> None:
    client.cookies.clear()
    admin_headers = auth_headers(admin_token(client, super_admin_credentials))
    order_headers = auth_headers(admin_token(client, order_manager_credentials))

    baseline = client.get("/api/v1/admin/reports/sales", headers=admin_headers).json()["data"]

    variant, base_price = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    order_detail = _place_and_confirm_cod_order(
        client, variant_id=variant["id"], order_headers=order_headers
    )

    after = client.get("/api/v1/admin/reports/sales", headers=admin_headers).json()["data"]

    assert after["total_orders"] == baseline["total_orders"] + 1
    assert Decimal(after["total_revenue"]) == Decimal(baseline["total_revenue"]) + Decimal(
        order_detail["total_amount"]
    )
    assert after["orders_by_status"].get("confirmed", 0) >= 1


def test_revenue_report_rejects_invalid_group_by(
    client: TestClient, super_admin_credentials
) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    response = client.get(
        "/api/v1/admin/reports/revenue", headers=headers, params={"group_by": "fortnight"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_GROUP_BY"


def test_revenue_report_returns_points(client: TestClient, super_admin_credentials) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    response = client.get(
        "/api/v1/admin/reports/revenue", headers=headers, params={"group_by": "day"}
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["group_by"] == "day"
    assert "points" in data


# --- Inventory (US-RPT-002) --------------------------------------------------


def test_inventory_report_flags_low_stock_variant(
    client: TestClient,
    super_admin_credentials,
    inventory_manager_credentials,
    content_manager_credentials,
) -> None:
    admin_headers = auth_headers(admin_token(client, super_admin_credentials))
    # Default reorder_threshold is 5; stocking only 2 keeps it at/under
    # threshold so it shows up in the low-stock list.
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=2
    )

    response = client.get("/api/v1/admin/reports/inventory", headers=admin_headers)
    assert response.status_code == 200, response.text
    low_stock_ids = {item["product_variant_id"] for item in response.json()["data"]["low_stock"]}
    assert variant["id"] in low_stock_ids


# --- Top-selling products (FR-RPT-005) --------------------------------------


def test_top_selling_products_includes_confirmed_order(
    client: TestClient,
    super_admin_credentials,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
) -> None:
    client.cookies.clear()
    admin_headers = auth_headers(admin_token(client, super_admin_credentials))
    order_headers = auth_headers(admin_token(client, order_manager_credentials))

    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    _place_and_confirm_cod_order(client, variant_id=variant["id"], order_headers=order_headers)

    response = client.get(
        "/api/v1/admin/reports/products/top-selling",
        headers=admin_headers,
        params={"limit": 100},
    )
    assert response.status_code == 200, response.text
    items = {item["product_variant_id"]: item for item in response.json()["data"]["items"]}
    assert variant["id"] in items
    assert items[variant["id"]]["quantity_sold"] >= 1


# --- Refunds (FR-RPT-006) ----------------------------------------------------


def test_refund_report_counts_requested_refund(
    client: TestClient,
    super_admin_credentials,
    inventory_manager_credentials,
    content_manager_credentials,
    order_manager_credentials,
) -> None:
    client.cookies.clear()
    admin_headers = auth_headers(admin_token(client, super_admin_credentials))
    order_headers = auth_headers(admin_token(client, order_manager_credentials))

    baseline = client.get("/api/v1/admin/reports/refunds", headers=admin_headers).json()["data"]
    baseline_requested = next(
        (row["count"] for row in baseline["by_status"] if row["status"] == "requested"), 0
    )

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

    after = client.get("/api/v1/admin/reports/refunds", headers=admin_headers).json()["data"]
    after_requested = next(
        (row["count"] for row in after["by_status"] if row["status"] == "requested"), 0
    )
    assert after_requested == baseline_requested + 1
    assert after["total_refunds"] == baseline["total_refunds"] + 1


# --- Customers (US-RPT-003) --------------------------------------------------


def test_customer_report_counts_new_registration(
    client: TestClient, super_admin_credentials
) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    baseline = client.get("/api/v1/admin/reports/customers", headers=headers).json()["data"]

    client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email("report-customer"),
            "password": "Passw0rd1",
            "full_name": "Report Customer",
        },
    )

    after = client.get("/api/v1/admin/reports/customers", headers=headers).json()["data"]
    assert after["total_customers"] == baseline["total_customers"] + 1
    assert after["new_customers"] >= baseline["new_customers"] + 1
