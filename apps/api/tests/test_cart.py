import uuid

from fastapi.testclient import TestClient

from tests.conftest import unique_email


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def register_customer(client: TestClient, **overrides) -> dict:
    payload = {"email": unique_email(), "password": "Passw0rd1", "full_name": "Cart Tester"}
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


# --- Guest cart basics -------------------------------------------------


def test_empty_guest_cart_shape(client: TestClient):
    client.cookies.clear()
    data = client.get("/api/v1/cart").json()["data"]
    assert data["item_count"] == 0
    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["total"] == "0.00"
    assert data["warnings"] == []


def test_guest_add_item_sets_cookie_and_computes_totals(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, base_price = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )

    response = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 2}
    )
    assert response.status_code == 201, response.text
    assert "cart_session_id" in response.cookies

    data = response.json()["data"]
    assert data["item_count"] == 2
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["quantity"] == 2
    assert item["unit_price_snapshot"] == base_price
    # Phase 4 validates against stock but doesn't reserve it (only
    # Phase 5's order placement does), so max_available == on-hand.
    assert item["max_available"] == 10
    assert data["subtotal"] == f"{float(base_price) * 2:.2f}"
    assert data["total"] == data["subtotal"]  # shipping/tax/discount are 0.00 placeholders


def test_adding_same_variant_twice_increments_a_single_line(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )

    client.post("/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1})
    response = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 2}
    )
    data = response.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3


def test_add_item_rejects_quantity_over_available_stock(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=3
    )

    response = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 5}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_add_item_for_draft_product_not_found(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"], status="draft")
    variant = create_stocked_variant(client, inv_headers, product["id"])

    response = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1}
    )
    assert response.status_code == 404


# --- Update / remove -----------------------------------------------------


def test_update_quantity_recalculates_totals(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, base_price = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1}
    ).json()["data"]
    item_id = add["items"][0]["id"]

    response = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 4})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"][0]["quantity"] == 4
    assert data["subtotal"] == f"{float(base_price) * 4:.2f}"


def test_update_quantity_rejects_over_stock(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=5
    )
    add = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1}
    ).json()["data"]
    item_id = add["items"][0]["id"]

    response = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 99})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_remove_item_empties_cart(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    add = client.post(
        "/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1}
    ).json()["data"]
    item_id = add["items"][0]["id"]

    response = client.delete(f"/api/v1/cart/items/{item_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"] == []
    assert data["item_count"] == 0


def test_item_not_in_cart_returns_404(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    client.get("/api/v1/cart")  # ensure this guest has an active cart of its own

    response = client.patch(f"/api/v1/cart/items/{uuid.uuid4()}", json={"quantity": 1})
    assert response.status_code == 404


# --- Guest isolation & authenticated carts --------------------------------


def test_guest_carts_are_isolated_by_session(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    client.post("/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 1})

    client.cookies.clear()  # simulate a different guest/browser
    data = client.get("/api/v1/cart").json()["data"]
    assert data["items"] == []


def test_authenticated_customer_cart_uses_token_not_cookie(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    customer = register_customer(client)
    headers = auth_headers(customer["access_token"])
    client.cookies.clear()  # a logged-in customer's cart must not depend on any cookie

    add = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"product_variant_id": variant["id"], "quantity": 2},
    )
    assert add.status_code == 201
    assert "cart_session_id" not in add.cookies

    fetched = client.get("/api/v1/cart", headers=headers).json()["data"]
    assert fetched["item_count"] == 2


# --- Merge on login (US-CRT-008 MVP slice) ----------------------------


def test_guest_cart_merges_into_customer_cart_on_register(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials
    )
    client.post("/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 2})
    assert "cart_session_id" in client.cookies

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "Passw0rd1", "full_name": "Merger"},
    )
    assert register_response.status_code == 201
    access_token = register_response.json()["data"]["access_token"]

    cart = client.get("/api/v1/cart", headers=auth_headers(access_token)).json()["data"]
    assert cart["item_count"] == 2
    assert cart["items"][0]["product_variant_id"] == variant["id"]


def test_guest_cart_merges_into_existing_customer_cart_on_login(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    client.cookies.clear()
    variant, _ = setup_stocked_variant(
        client, inventory_manager_credentials, content_manager_credentials, stock=10
    )
    customer = register_customer(client, email=unique_email())
    email = customer["customer"]["email"]

    # Customer already has 1 unit in their own cart from a prior session.
    client.post(
        "/api/v1/cart/items",
        headers=auth_headers(customer["access_token"]),
        json={"product_variant_id": variant["id"], "quantity": 1},
    )

    # Then browses as a guest (different device) and adds 2 more of the same variant.
    client.cookies.clear()
    client.post("/api/v1/cart/items", json={"product_variant_id": variant["id"], "quantity": 2})

    login_response = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": "Passw0rd1"}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["data"]["access_token"]

    cart = client.get("/api/v1/cart", headers=auth_headers(access_token)).json()["data"]
    assert cart["item_count"] == 3  # merged: 1 (existing) + 2 (guest)
    assert len(cart["items"]) == 1  # same variant, still a single line
