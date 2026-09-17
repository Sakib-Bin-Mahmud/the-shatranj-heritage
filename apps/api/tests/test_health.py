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
    # auth, customers, and orders have gained real endpoints since Phase 1
    # (see tests/test_auth.py, tests/test_customers.py) — this only
    # covers modules still at the Phase 0 placeholder stage.
    for module in (
        "catalog",
        "inventory",
        "cart",
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
