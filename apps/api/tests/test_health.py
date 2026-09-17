from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_module_scaffolds_are_wired() -> None:
    for module in (
        "auth",
        "catalog",
        "inventory",
        "cart",
        "orders",
        "payments",
        "shipping",
        "cms",
        "admin",
        "notifications",
    ):
        response = client.get(f"/api/v1/{module}/")
        assert response.status_code == 200, module
        assert response.json() == {"module": module, "status": "scaffolded"}


def test_unknown_route_returns_standard_error_envelope() -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "HTTP_404"
