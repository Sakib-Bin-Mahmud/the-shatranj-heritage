from fastapi.testclient import TestClient

from tests.conftest import unique_email


def register_and_login(client: TestClient) -> tuple[str, dict]:
    email = unique_email()
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd1", "full_name": "Address Test"},
    )
    data = response.json()["data"]
    return data["access_token"], data["customer"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/customers/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_get_and_update_profile(client: TestClient) -> None:
    token, customer = register_and_login(client)

    profile = client.get("/api/v1/customers/me", headers=auth_headers(token))
    assert profile.status_code == 200
    assert profile.json()["data"]["id"] == customer["id"]

    updated = client.patch(
        "/api/v1/customers/me", headers=auth_headers(token), json={"full_name": "Updated Name"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["full_name"] == "Updated Name"


def test_first_address_becomes_default_automatically(client: TestClient) -> None:
    token, _ = register_and_login(client)

    response = client.post(
        "/api/v1/customers/me/addresses",
        headers=auth_headers(token),
        json={
            "recipient_name": "Karim Ahmed",
            "phone": "+8801711111111",
            "address_line1": "House 1",
            "city": "Dhaka",
            "district": "Dhaka",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["is_default"] is True


def test_setting_new_default_address_unsets_previous(client: TestClient) -> None:
    token, _ = register_and_login(client)
    headers = auth_headers(token)

    first = client.post(
        "/api/v1/customers/me/addresses",
        headers=headers,
        json={
            "recipient_name": "A",
            "phone": "+8801711111111",
            "address_line1": "Addr 1",
            "city": "Dhaka",
            "district": "Dhaka",
        },
    ).json()["data"]

    second = client.post(
        "/api/v1/customers/me/addresses",
        headers=headers,
        json={
            "recipient_name": "B",
            "phone": "+8801711111112",
            "address_line1": "Addr 2",
            "city": "Dhaka",
            "district": "Dhaka",
            "is_default": True,
        },
    ).json()["data"]

    listing = client.get("/api/v1/customers/me/addresses", headers=headers).json()["data"]
    by_id = {a["id"]: a for a in listing}
    assert by_id[first["id"]]["is_default"] is False
    assert by_id[second["id"]]["is_default"] is True


def test_deleting_default_address_promotes_another(client: TestClient) -> None:
    token, _ = register_and_login(client)
    headers = auth_headers(token)

    first = client.post(
        "/api/v1/customers/me/addresses",
        headers=headers,
        json={
            "recipient_name": "A",
            "phone": "+8801711111111",
            "address_line1": "Addr 1",
            "city": "Dhaka",
            "district": "Dhaka",
        },
    ).json()["data"]
    second = client.post(
        "/api/v1/customers/me/addresses",
        headers=headers,
        json={
            "recipient_name": "B",
            "phone": "+8801711111112",
            "address_line1": "Addr 2",
            "city": "Dhaka",
            "district": "Dhaka",
        },
    ).json()["data"]

    delete_response = client.delete(
        f"/api/v1/customers/me/addresses/{first['id']}", headers=headers
    )
    assert delete_response.status_code == 200

    listing = client.get("/api/v1/customers/me/addresses", headers=headers).json()["data"]
    remaining = next(a for a in listing if a["id"] == second["id"])
    assert remaining["is_default"] is True


def test_cannot_access_another_customers_address(client: TestClient) -> None:
    token_a, _ = register_and_login(client)
    token_b, _ = register_and_login(client)

    address = client.post(
        "/api/v1/customers/me/addresses",
        headers=auth_headers(token_a),
        json={
            "recipient_name": "A",
            "phone": "+8801711111111",
            "address_line1": "Addr 1",
            "city": "Dhaka",
            "district": "Dhaka",
        },
    ).json()["data"]

    response = client.patch(
        f"/api/v1/customers/me/addresses/{address['id']}",
        headers=auth_headers(token_b),
        json={"city": "Chittagong"},
    )
    assert response.status_code == 404


def test_orders_history_stub_requires_auth_and_is_empty(client: TestClient) -> None:
    unauthenticated = client.get("/api/v1/orders/")
    assert unauthenticated.status_code == 401

    token, _ = register_and_login(client)
    response = client.get("/api/v1/orders/", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["data"] == {
        "items": [],
        "meta": {"page": 1, "limit": 20, "total": 0, "total_pages": 0},
    }


def test_admin_customer_endpoints_require_admin_token(client: TestClient) -> None:
    token, _ = register_and_login(client)
    response = client.get("/api/v1/admin/customers", headers=auth_headers(token))
    assert response.status_code == 401


def test_admin_can_list_get_and_suspend_customer(
    client: TestClient, super_admin_credentials
) -> None:
    customer_token, customer = register_and_login(client)

    admin_login = client.post("/api/v1/admin/auth/login", json=super_admin_credentials)
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = auth_headers(admin_token)

    listing = client.get(
        f"/api/v1/admin/customers?search={customer['email']}", headers=admin_headers
    )
    assert listing.status_code == 200
    assert listing.json()["data"]["meta"]["total"] == 1

    detail = client.get(f"/api/v1/admin/customers/{customer['id']}", headers=admin_headers)
    assert detail.status_code == 200

    suspend = client.patch(
        f"/api/v1/admin/customers/{customer['id']}/status",
        headers=admin_headers,
        json={"status": "suspended"},
    )
    assert suspend.status_code == 200
    assert suspend.json()["data"]["status"] == "suspended"

    blocked_login = client.post(
        "/api/v1/auth/login", json={"identifier": customer["email"], "password": "Passw0rd1"}
    )
    assert blocked_login.status_code == 401
    # Confirm the customer's own (now stale) access token still decodes
    # fine but the account is suspended — get_current_customer must
    # reject it going forward too.
    profile = client.get("/api/v1/customers/me", headers=auth_headers(customer_token))
    assert profile.status_code == 401


def test_customer_support_can_read_but_not_manage(
    client: TestClient, customer_support_credentials
) -> None:
    """RBAC: customer_support only has customers.read, not
    customers.manage (see the role_permissions seed migration)."""
    _, customer = register_and_login(client)

    login = client.post("/api/v1/admin/auth/login", json=customer_support_credentials)
    headers = auth_headers(login.json()["data"]["access_token"])

    read = client.get(f"/api/v1/admin/customers/{customer['id']}", headers=headers)
    assert read.status_code == 200

    manage = client.patch(
        f"/api/v1/admin/customers/{customer['id']}/status",
        headers=headers,
        json={"status": "suspended"},
    )
    assert manage.status_code == 403
    assert manage.json()["error"]["code"] == "FORBIDDEN"


def test_admin_get_nonexistent_customer_returns_404(
    client: TestClient, super_admin_credentials
) -> None:
    admin_login = client.post("/api/v1/admin/auth/login", json=super_admin_credentials)
    admin_token = admin_login.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/admin/customers/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404
