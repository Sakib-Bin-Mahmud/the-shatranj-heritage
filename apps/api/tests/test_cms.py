import uuid

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient, credentials: dict) -> str:
    response = client.post("/api/v1/admin/auth/login", json=credentials)
    return response.json()["data"]["access_token"]


def test_public_pages_index_only_lists_published(
    client: TestClient, content_manager_credentials
) -> None:
    headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]

    published = client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={
            "slug": f"published-{suffix}",
            "title": "Published Page",
            "body": "Visible body.",
            "is_published": True,
        },
    )
    assert published.status_code == 201, published.text

    draft = client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={
            "slug": f"draft-{suffix}",
            "title": "Draft Page",
            "body": "Hidden body.",
            "is_published": False,
        },
    )
    assert draft.status_code == 201, draft.text

    index = client.get("/api/v1/content/pages").json()["data"]
    slugs = {page["slug"] for page in index}
    assert f"published-{suffix}" in slugs
    assert f"draft-{suffix}" not in slugs


def test_public_get_unpublished_page_returns_404(
    client: TestClient, content_manager_credentials
) -> None:
    headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]
    client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={
            "slug": f"hidden-{suffix}",
            "title": "Hidden",
            "body": "Body.",
            "is_published": False,
        },
    )

    response = client.get(f"/api/v1/content/pages/hidden-{suffix}")
    assert response.status_code == 404


def test_publishing_a_page_sets_published_at(
    client: TestClient, content_manager_credentials
) -> None:
    headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]
    page = client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={
            "slug": f"toggle-{suffix}",
            "title": "Toggle",
            "body": "Body.",
            "is_published": False,
        },
    ).json()["data"]
    assert page["published_at"] is None

    published = client.patch(
        f"/api/v1/admin/content/pages/{page['id']}",
        headers=headers,
        json={"is_published": True},
    )
    assert published.status_code == 200, published.text
    assert published.json()["data"]["published_at"] is not None

    unpublished = client.patch(
        f"/api/v1/admin/content/pages/{page['id']}",
        headers=headers,
        json={"is_published": False},
    ).json()["data"]
    assert unpublished["published_at"] is None


def test_admin_get_page_returns_body_for_draft(
    client: TestClient, content_manager_credentials
) -> None:
    """The public GET /content/pages/{slug} 404s on a draft, so the
    admin edit form needs its own way to fetch one's full body."""
    headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]
    page = client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={
            "slug": f"draft-detail-{suffix}",
            "title": "Draft Detail",
            "body": "Only visible to staff.",
            "is_published": False,
        },
    ).json()["data"]

    response = client.get(f"/api/v1/admin/content/pages/{page['id']}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["body"] == "Only visible to staff."
    assert data["is_published"] is False


def test_admin_get_page_requires_cms_permission(
    client: TestClient, content_manager_credentials, customer_support_credentials
) -> None:
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]
    page = client.post(
        "/api/v1/admin/content/pages",
        headers=content_headers,
        json={"slug": f"gated-{suffix}", "title": "Gated", "body": "Body."},
    ).json()["data"]

    support_headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get(f"/api/v1/admin/content/pages/{page['id']}", headers=support_headers)
    assert response.status_code == 403


def test_duplicate_slug_rejected(client: TestClient, content_manager_credentials) -> None:
    headers = auth_headers(admin_token(client, content_manager_credentials))
    suffix = uuid.uuid4().hex[:8]
    payload = {"slug": f"dupe-{suffix}", "title": "First", "body": "Body."}
    first = client.post("/api/v1/admin/content/pages", headers=headers, json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/admin/content/pages", headers=headers, json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "SLUG_ALREADY_EXISTS"


def test_non_content_manager_cannot_write_pages(
    client: TestClient, customer_support_credentials
) -> None:
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.post(
        "/api/v1/admin/content/pages",
        headers=headers,
        json={"slug": f"forbidden-{uuid.uuid4().hex[:8]}", "title": "Nope", "body": "Body."},
    )
    assert response.status_code == 403


def test_seeded_policy_pages_are_publicly_visible(client: TestClient) -> None:
    """NFR-COM-001: the five legally-required policy pages seeded by
    the Phase 7 migration must be live and publishable from day one."""
    for slug in (
        "terms-and-conditions",
        "privacy-policy",
        "return-and-refund-policy",
        "shipping-policy",
        "warranty-policy",
    ):
        response = client.get(f"/api/v1/content/pages/{slug}")
        assert response.status_code == 200, slug
        assert response.json()["data"]["page_type"] == "policy"
