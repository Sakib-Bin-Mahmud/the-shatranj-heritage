from fastapi.testclient import TestClient

from tests.conftest import unique_email


def test_subscribe_creates_subscriber(client: TestClient) -> None:
    email = unique_email("newsletter")
    response = client.post("/api/v1/newsletter/subscribe", json={"email": email})
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["email"] == email
    assert data["is_active"] is True


def test_subscribe_is_idempotent_for_same_email(client: TestClient) -> None:
    email = unique_email("newsletter")

    first = client.post("/api/v1/newsletter/subscribe", json={"email": email})
    assert first.status_code == 201, first.text

    second = client.post("/api/v1/newsletter/subscribe", json={"email": email})
    assert second.status_code == 201, second.text
    assert second.json()["data"]["email"] == email


def test_subscribe_normalizes_email_case(client: TestClient) -> None:
    email = unique_email("Newsletter")

    client.post("/api/v1/newsletter/subscribe", json={"email": email.upper()})
    second = client.post("/api/v1/newsletter/subscribe", json={"email": email.lower()})

    assert second.status_code == 201, second.text
    assert second.json()["data"]["email"] == email.lower()


def test_subscribe_rejects_invalid_email(client: TestClient) -> None:
    response = client.post("/api/v1/newsletter/subscribe", json={"email": "not-an-email"})
    assert response.status_code == 422
