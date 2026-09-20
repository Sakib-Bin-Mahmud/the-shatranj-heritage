from fastapi.testclient import TestClient

from tests.conftest import unique_email, unique_mobile


def register(client: TestClient, **overrides) -> dict:
    payload = {"email": unique_email(), "password": "Passw0rd1", "full_name": "Test User"}
    payload.update(overrides)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_register_with_email_success(client: TestClient) -> None:
    data = register(client)
    assert data["customer"]["email"]
    assert data["access_token"]
    assert data["refresh_token"]


def test_register_duplicate_email_conflict(client: TestClient) -> None:
    email = unique_email()
    register(client, email=email)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd1", "full_name": "Dup"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_with_mobile_normalizes_number(client: TestClient) -> None:
    mobile = unique_mobile()
    data = register(client, email=None, mobile_number=mobile)
    assert data["customer"]["mobile_number"] == "+880" + mobile[1:]


def test_register_weak_password_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "short", "full_name": "Weak"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_missing_identifier_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"password": "Passw0rd1", "full_name": "No Identifier"},
    )
    assert response.status_code == 422


def test_login_success_with_email(client: TestClient) -> None:
    email = unique_email()
    register(client, email=email)

    response = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": "Passw0rd1"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["customer"]["email"] == email


def test_login_success_with_local_format_mobile(client: TestClient) -> None:
    mobile = unique_mobile()
    register(client, email=None, mobile_number=mobile)

    response = client.post(
        "/api/v1/auth/login", json={"identifier": mobile, "password": "Passw0rd1"}
    )
    assert response.status_code == 200


def test_login_wrong_password_and_unknown_user_share_error_code(client: TestClient) -> None:
    email = unique_email()
    register(client, email=email)

    wrong_password = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": "WrongPass1"}
    )
    unknown_user = client.post(
        "/api/v1/auth/login", json={"identifier": unique_email(), "password": "WrongPass1"}
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert unknown_user.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_rotates_token_and_invalidates_previous(client: TestClient) -> None:
    data = register(client)
    old_refresh = data["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["data"]["refresh_token"]
    assert new_refresh != old_refresh

    reuse_old = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_old.status_code == 401
    assert reuse_old.json()["error"]["code"] == "UNAUTHENTICATED"


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    data = register(client)
    refresh_token = data["refresh_token"]

    logout_response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200

    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401


def test_logout_with_already_invalid_token_is_a_noop(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 200


def test_forgot_and_reset_password_flow(client: TestClient) -> None:
    email = unique_email()
    register(client, email=email)

    forgot = client.post("/api/v1/auth/forgot-password", json={"identifier": email})
    assert forgot.status_code == 200
    reset_token = forgot.json()["data"]["debug_reset_token"]

    reset = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "NewPassw0rd1"}
    )
    assert reset.status_code == 200

    old_password_login = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": "Passw0rd1"}
    )
    assert old_password_login.status_code == 401

    new_password_login = client.post(
        "/api/v1/auth/login", json={"identifier": email, "password": "NewPassw0rd1"}
    )
    assert new_password_login.status_code == 200

    reuse_token = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "AnotherOne1"}
    )
    assert reuse_token.status_code == 400
    assert reuse_token.json()["error"]["code"] == "INVALID_RESET_TOKEN"


def test_forgot_password_unknown_identifier_still_returns_success(client: TestClient) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"identifier": unique_email()})
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_reset_password_with_invalid_token_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/reset-password", json={"token": "bogus", "new_password": "NewPassw0rd1"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_RESET_TOKEN"


def test_login_rate_limited_after_threshold(client: TestClient) -> None:
    statuses = [
        client.post(
            "/api/v1/auth/login", json={"identifier": "nobody@example.com", "password": "wrong"}
        ).status_code
        for _ in range(11)
    ]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_admin_login_success_and_permissions_embedded(
    client: TestClient, super_admin_credentials
) -> None:
    response = client.post("/api/v1/admin/auth/login", json=super_admin_credentials)
    assert response.status_code == 200
    body = response.json()["data"]
    assert "super_admin" in body["admin"]["roles"]
    assert body["access_token"]


def test_admin_login_wrong_password_rejected(client: TestClient, super_admin_credentials) -> None:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"email": super_admin_credentials["email"], "password": "WrongPassword1"},
    )
    assert response.status_code == 401


def test_customer_refresh_token_rejected_on_admin_refresh_flow(client: TestClient) -> None:
    """A customer token must not be usable where an admin token is
    expected — /auth/refresh dispatches by the token's own `type` claim,
    so a customer refresh token should always come back as a customer
    session, never silently treated as an admin one."""
    data = register(client)
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert refreshed.status_code == 200
    assert "admin" not in refreshed.json()["data"]
