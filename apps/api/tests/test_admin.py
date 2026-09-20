from fastapi.testclient import TestClient

from tests.conftest import unique_email
from tests.test_shipping import add_to_cart, inline_address, setup_stocked_variant


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


# --- Roles (FR-ADM-007) ----------------------------------------------------


def test_list_roles_includes_permissions(client: TestClient, super_admin_credentials) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    response = client.get("/api/v1/admin/roles", headers=headers)
    assert response.status_code == 200, response.text

    roles = {r["name"]: r for r in response.json()["data"]}
    assert "super_admin" in roles
    assert "staff.manage" in roles["super_admin"]["permissions"]
    assert "content_manager" in roles
    assert "cms.write" in roles["content_manager"]["permissions"]


def test_non_staff_manager_cannot_list_roles(
    client: TestClient, customer_support_credentials
) -> None:
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get("/api/v1/admin/roles", headers=headers)
    assert response.status_code == 403


# --- Staff accounts (US-ADM-003/004) ---------------------------------------


def test_create_staff_user_and_login(client: TestClient, super_admin_credentials) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    email = unique_email("staff")
    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": "StaffPass123",
            "full_name": "New Staff",
            "role_names": ["customer_support"],
        },
    )
    assert response.status_code == 201, response.text
    staff = response.json()["data"]
    assert staff["roles"] == ["customer_support"]

    login = client.post(
        "/api/v1/admin/auth/login", json={"email": email, "password": "StaffPass123"}
    )
    assert login.status_code == 200


def test_create_staff_user_unknown_role_rejected(
    client: TestClient, super_admin_credentials
) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": unique_email("staff"),
            "password": "StaffPass123",
            "full_name": "Bad Role",
            "role_names": ["not_a_real_role"],
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNKNOWN_ROLE"


def test_assign_roles_updates_staff_and_records_audit_log(
    client: TestClient, super_admin_credentials
) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    email = unique_email("staff")
    staff = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": "StaffPass123",
            "full_name": "Reassign Me",
            "role_names": ["customer_support"],
        },
    ).json()["data"]

    response = client.patch(
        f"/api/v1/admin/users/{staff['id']}/roles",
        headers=headers,
        json={"role_names": ["order_manager"]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["roles"] == ["order_manager"]

    audit = client.get(
        "/api/v1/admin/audit-logs",
        headers=headers,
        params={"entity_type": "admin_user"},
    ).json()["data"]["items"]
    matching = [
        entry
        for entry in audit
        if entry["entity_id"] == staff["id"] and entry["action"] == "staff.roles_updated"
    ]
    assert len(matching) == 1
    assert matching[0]["before"]["roles"] == ["customer_support"]
    assert matching[0]["after"]["roles"] == ["order_manager"]


def test_non_super_admin_cannot_create_staff(
    client: TestClient, content_manager_credentials
) -> None:
    headers = auth_headers(admin_token(client, content_manager_credentials))
    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": unique_email("staff"),
            "password": "StaffPass123",
            "full_name": "Nope",
            "role_names": ["customer_support"],
        },
    )
    assert response.status_code == 403


# --- Audit log viewer (NFR-AUD-001) -----------------------------------------


def test_audit_read_requires_permission(client: TestClient, customer_support_credentials) -> None:
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert response.status_code == 403


def test_super_admin_can_read_audit_log(client: TestClient, super_admin_credentials) -> None:
    headers = auth_headers(admin_token(client, super_admin_credentials))
    response = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()["data"]


# --- Shipping-rate settings (BR-SHP-002) ------------------------------------


def test_shipping_rate_update_changes_checkout_cost(
    client: TestClient,
    super_admin_credentials,
    inventory_manager_credentials,
    content_manager_credentials,
) -> None:
    client.cookies.clear()
    admin_headers = auth_headers(admin_token(client, super_admin_credentials))

    rates = client.get("/api/v1/admin/settings/shipping-rates", headers=admin_headers).json()[
        "data"
    ]
    dhaka_standard = next(r for r in rates if r["zone"] == "dhaka" and r["method"] == "standard")
    original_rate = dhaka_standard["base_rate"]

    try:
        updated = client.patch(
            f"/api/v1/admin/settings/shipping-rates/{dhaka_standard['id']}",
            headers=admin_headers,
            json={"base_rate": "999.00"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["base_rate"] == "999.00"

        variant, _ = setup_stocked_variant(
            client, inventory_manager_credentials, content_manager_credentials
        )
        add_to_cart(client, variant["id"], 1)
        quote = client.post(
            "/api/v1/checkout/quote",
            json={"address": inline_address(district="Dhaka"), "shipping_method": "standard"},
        ).json()["data"]
        assert quote["shipping_amount"] == "999.00"
    finally:
        client.patch(
            f"/api/v1/admin/settings/shipping-rates/{dhaka_standard['id']}",
            headers=admin_headers,
            json={"base_rate": original_rate},
        )


def test_non_super_admin_cannot_manage_settings(
    client: TestClient, order_manager_credentials
) -> None:
    headers = auth_headers(admin_token(client, order_manager_credentials))
    response = client.get("/api/v1/admin/settings/shipping-rates", headers=headers)
    assert response.status_code == 403
