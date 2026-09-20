import io
import uuid

from fastapi.testclient import TestClient

FAKE_JPEG_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-content-for-testing"


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


def create_variant(client: TestClient, headers: dict, product_id: str, **overrides) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {"sku": f"VAR-{suffix}", "variant_name": "Standard"}
    payload.update(overrides)
    response = client.post(
        f"/api/v1/admin/products/{product_id}/variants", headers=headers, json=payload
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def restock(client: TestClient, headers: dict, variant_id: str, quantity: int) -> None:
    response = client.patch(
        f"/api/v1/admin/inventory/{variant_id}/adjust",
        headers=headers,
        json={"change_type": "restock", "quantity_delta": quantity, "note": "test restock"},
    )
    assert response.status_code == 200, response.text


# --- Categories --------------------------------------------------------


def test_category_crud_and_public_tree(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    content_headers = auth_headers(admin_token(client, content_manager_credentials))

    parent = create_category(client, content_headers)
    child = create_category(client, content_headers, parent_category_id=parent["id"])

    tree = client.get("/api/v1/categories").json()["data"]
    parent_node = next(c for c in tree if c["id"] == parent["id"])
    assert any(c["id"] == child["id"] for c in parent_node["children"])

    detail = client.get(f"/api/v1/categories/{parent['slug']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == parent["id"]

    updated = client.patch(
        f"/api/v1/admin/categories/{child['id']}", headers=content_headers, json={"name": "Renamed"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Renamed"

    deactivated = client.delete(f"/api/v1/admin/categories/{child['id']}", headers=content_headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["is_active"] is False

    # Deactivated categories drop out of the public tree.
    tree_after = client.get("/api/v1/categories").json()["data"]
    parent_after = next(c for c in tree_after if c["id"] == parent["id"])
    assert not any(c["id"] == child["id"] for c in parent_after["children"])

    # But still visible to admins via include_inactive listing.
    admin_list = client.get("/api/v1/admin/categories", headers=content_headers).json()["data"]
    assert any(c["id"] == child["id"] for c in admin_list)


def test_category_duplicate_slug_conflict(client: TestClient, content_manager_credentials):
    headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, headers)

    response = client.post(
        "/api/v1/admin/categories", headers=headers, json={"name": "Dup", "slug": category["slug"]}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLUG_ALREADY_EXISTS"


def test_category_self_parent_rejected(client: TestClient, content_manager_credentials):
    headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, headers)

    response = client.patch(
        f"/api/v1/admin/categories/{category['id']}",
        headers=headers,
        json={"parent_category_id": category["id"]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PARENT"


def test_inventory_manager_cannot_write_categories(
    client: TestClient, inventory_manager_credentials
):
    headers = auth_headers(admin_token(client, inventory_manager_credentials))
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "X", "slug": f"x-{uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# --- Products & variants -------------------------------------------------


def test_product_crud_lifecycle(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))

    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"], status="draft")
    assert product["status"] == "draft"

    # Draft products are invisible publicly...
    public = client.get(f"/api/v1/products/{product['slug']}")
    assert public.status_code == 404

    # ...but visible to admins.
    admin_get = client.get(f"/api/v1/admin/products/{product['id']}", headers=inv_headers)
    assert admin_get.status_code == 200

    updated = client.patch(
        f"/api/v1/admin/products/{product['id']}",
        headers=inv_headers,
        json={"status": "active", "brand": "Shatranj"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "active"

    public_after = client.get(f"/api/v1/products/{product['slug']}")
    assert public_after.status_code == 200

    archived = client.delete(f"/api/v1/admin/products/{product['id']}", headers=inv_headers)
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"

    public_after_archive = client.get(f"/api/v1/products/{product['slug']}")
    assert public_after_archive.status_code == 404


def test_product_duplicate_sku_conflict(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])

    response = client.post(
        "/api/v1/admin/products",
        headers=inv_headers,
        json={
            "sku": product["sku"],
            "name": "Dup",
            "slug": f"dup-{uuid.uuid4().hex[:8]}",
            "category_id": category["id"],
            "base_price": "100.00",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SKU_ALREADY_EXISTS"


def test_product_requires_existing_category(client: TestClient, inventory_manager_credentials):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    response = client.post(
        "/api/v1/admin/products",
        headers=inv_headers,
        json={
            "sku": f"SKU-{uuid.uuid4().hex[:8]}",
            "name": "No Category",
            "slug": f"no-cat-{uuid.uuid4().hex[:8]}",
            "category_id": str(uuid.uuid4()),
            "base_price": "100.00",
        },
    )
    assert response.status_code == 404


def test_first_variant_becomes_default_and_gets_inventory_row(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])

    result = client.post(
        f"/api/v1/admin/products/{product['id']}/variants",
        headers=inv_headers,
        json={"sku": f"VAR-{uuid.uuid4().hex[:8]}", "variant_name": "Only Variant"},
    )
    assert result.status_code == 201
    variant = result.json()["data"]["variants"][0]
    assert variant["is_default"] is True
    assert variant["quantity_available"] == 0  # inventory row auto-created at zero


def test_setting_new_default_variant_unsets_previous(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])

    first = create_variant(client, inv_headers, product["id"])
    second = create_variant(client, inv_headers, product["id"], is_default=True)

    detail = client.get(f"/api/v1/admin/products/{product['id']}", headers=inv_headers).json()[
        "data"
    ]
    by_id = {v["id"]: v for v in detail["variants"]}
    assert by_id[first["variants"][-1]["id"]]["is_default"] is False
    assert by_id[second["variants"][-1]["id"]]["is_default"] is True


def test_variant_archive_is_not_hard_delete(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])
    result = create_variant(client, inv_headers, product["id"])
    variant_id = result["variants"][-1]["id"]

    response = client.delete(
        f"/api/v1/admin/products/{product['id']}/variants/{variant_id}", headers=inv_headers
    )
    assert response.status_code == 200
    variant = next(v for v in response.json()["data"]["variants"] if v["id"] == variant_id)
    assert variant["status"] == "archived"


# --- Public browsing/search -----------------------------------------------


def test_public_product_list_filters_and_sorts(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)

    cheap = create_product(
        client, inv_headers, category["id"], name="Cheap Item", base_price="500.00"
    )
    expensive = create_product(
        client, inv_headers, category["id"], name="Expensive Item", base_price="9000.00"
    )
    create_variant(client, inv_headers, cheap["id"], attributes={"material": "brass"})
    create_variant(client, inv_headers, expensive["id"], attributes={"material": "marble"})

    by_category = client.get(f"/api/v1/products?category={category['slug']}").json()["data"]
    assert by_category["meta"]["total"] == 2

    price_asc = client.get(f"/api/v1/products?category={category['slug']}&sort=price_asc").json()[
        "data"
    ]
    assert [p["id"] for p in price_asc["items"]] == [cheap["id"], expensive["id"]]

    price_filtered = client.get(
        f"/api/v1/products?category={category['slug']}&price_min=1000"
    ).json()["data"]
    assert [p["id"] for p in price_filtered["items"]] == [expensive["id"]]

    material_filtered = client.get(
        f"/api/v1/products?category={category['slug']}&material=marble"
    ).json()["data"]
    assert [p["id"] for p in material_filtered["items"]] == [expensive["id"]]

    q_filtered = client.get("/api/v1/products?q=Cheap+Item").json()["data"]
    assert any(p["id"] == cheap["id"] for p in q_filtered["items"])


def test_availability_filter_requires_in_stock_variant(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)

    out_of_stock = create_product(client, inv_headers, category["id"])
    create_variant(client, inv_headers, out_of_stock["id"])

    in_stock = create_product(client, inv_headers, category["id"])
    variant = create_variant(client, inv_headers, in_stock["id"])
    restock(client, inv_headers, variant["variants"][-1]["id"], 10)

    result = client.get(
        f"/api/v1/products?category={category['slug']}&availability=in_stock"
    ).json()["data"]
    ids = [p["id"] for p in result["items"]]
    assert in_stock["id"] in ids
    assert out_of_stock["id"] not in ids


def test_search_ranks_name_matches_above_description_matches(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)

    # Created in reverse of the expected result order, so the assertion
    # below can only pass because of the name/description weighting
    # (search_vector's setweight('A'/'B')) — not because of insertion
    # or scan order.
    description_match = create_product(
        client,
        inv_headers,
        category["id"],
        name="Collector's Board",
        description="Comes with a handcrafted rosewood box.",
    )
    name_match = create_product(
        client,
        inv_headers,
        category["id"],
        name="Handcrafted Rosewood Chess Set",
        description="A fine set for any collector.",
    )

    result = client.get("/api/v1/products?q=rosewood").json()["data"]
    ids = [p["id"] for p in result["items"]]
    assert ids.index(name_match["id"]) < ids.index(description_match["id"])


def test_search_matches_sku(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)

    suffix = uuid.uuid4().hex[:8]
    product = create_product(client, inv_headers, category["id"], sku=f"UNIQUE-SKU-{suffix}")

    result = client.get(f"/api/v1/products?q=UNIQUE-SKU-{suffix}").json()["data"]
    assert [p["id"] for p in result["items"]] == [product["id"]]


def test_featured_filter(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)

    featured = create_product(client, inv_headers, category["id"], is_featured=True)
    plain = create_product(client, inv_headers, category["id"], is_featured=False)

    result = client.get(f"/api/v1/products?category={category['slug']}&featured=true").json()[
        "data"
    ]
    ids = [p["id"] for p in result["items"]]
    assert featured["id"] in ids
    assert plain["id"] not in ids
    assert all(p["is_featured"] for p in result["items"])


def test_no_results_search_returns_suggestions(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    create_product(client, inv_headers, category["id"], is_featured=True)

    nonsense = uuid.uuid4().hex
    result = client.get(f"/api/v1/products?q={nonsense}").json()["data"]
    assert result["meta"]["total"] == 0
    assert "suggestions" in result
    # Both lists are capped (top-N), so with many categories/products
    # accumulated across the suite we only assert the shape and that
    # returned featured products really are featured — not that this
    # test's own category/product survives the cap.
    assert isinstance(result["suggestions"]["categories"], list)
    assert result["suggestions"]["categories"]
    assert isinstance(result["suggestions"]["featured_products"], list)
    assert all(p["is_featured"] for p in result["suggestions"]["featured_products"])


def test_related_products_same_category(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    other_category = create_category(client, content_headers)

    product = create_product(client, inv_headers, category["id"])
    sibling = create_product(client, inv_headers, category["id"])
    unrelated = create_product(client, inv_headers, other_category["id"])

    related = client.get(f"/api/v1/products/{product['id']}/related").json()["data"]
    ids = [p["id"] for p in related]
    assert sibling["id"] in ids
    assert unrelated["id"] not in ids
    assert product["id"] not in ids


# --- Artisans --------------------------------------------------------------


def test_artisan_crud(client: TestClient, inventory_manager_credentials):
    headers = auth_headers(admin_token(client, inventory_manager_credentials))
    created = client.post(
        "/api/v1/admin/artisans",
        headers=headers,
        json={"name": "Karim Woodworks", "region": "Sylhet"},
    )
    assert created.status_code == 201
    artisan_id = created.json()["data"]["id"]

    updated = client.patch(
        f"/api/v1/admin/artisans/{artisan_id}", headers=headers, json={"bio": "Est. 1990"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["bio"] == "Est. 1990"

    listing = client.get("/api/v1/admin/artisans", headers=headers).json()["data"]
    assert any(a["id"] == artisan_id for a in listing)


# --- Inventory ---------------------------------------------------------


def test_inventory_adjust_rejects_negative_stock(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])
    variant = create_variant(client, inv_headers, product["id"])
    variant_id = variant["variants"][-1]["id"]

    response = client.patch(
        f"/api/v1/admin/inventory/{variant_id}/adjust",
        headers=inv_headers,
        json={"change_type": "damage", "quantity_delta": -5},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NEGATIVE_STOCK"


def test_inventory_transaction_history_and_low_stock_filter(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])
    variant = create_variant(client, inv_headers, product["id"])
    variant_id = variant["variants"][-1]["id"]

    restock(client, inv_headers, variant_id, 10)
    client.patch(
        f"/api/v1/admin/inventory/{variant_id}/adjust",
        headers=inv_headers,
        json={"change_type": "damage", "quantity_delta": -8},
    )

    history = client.get(
        f"/api/v1/admin/inventory/{variant_id}/transactions", headers=inv_headers
    ).json()["data"]
    assert history["meta"]["total"] == 2

    # limit=100: other tests in the suite create their own low-stock
    # variants, so this must not assume its own lands on the default
    # first page of 20 when the full suite runs more than once against
    # the same (non-freshly-migrated) database.
    low_stock = client.get(
        "/api/v1/admin/inventory", headers=inv_headers, params={"low_stock": True, "limit": 100}
    ).json()["data"]
    assert any(item["product_variant_id"] == variant_id for item in low_stock["items"])


def test_customer_support_cannot_access_inventory(client: TestClient, customer_support_credentials):
    headers = auth_headers(admin_token(client, customer_support_credentials))
    response = client.get("/api/v1/admin/inventory", headers=headers)
    assert response.status_code == 403


# --- Images ------------------------------------------------------------


def test_image_upload_sets_primary_and_delete_removes_it(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])

    upload = client.post(
        f"/api/v1/admin/products/{product['id']}/images",
        headers=inv_headers,
        files={"file": ("test.jpg", io.BytesIO(FAKE_JPEG_BYTES), "image/jpeg")},
        data={"is_primary": "true"},
    )
    assert upload.status_code == 201, upload.text
    images = upload.json()["data"]["images"]
    assert len(images) == 1
    assert images[0]["is_primary"] is True
    image_id = images[0]["id"]

    summary = client.get(f"/api/v1/products?category={category['slug']}").json()["data"]
    assert summary["items"][0]["primary_image_url"] == images[0]["url"]

    deleted = client.delete(
        f"/api/v1/admin/products/{product['id']}/images/{image_id}", headers=inv_headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["images"] == []


def test_image_upload_rejects_unsupported_type(
    client: TestClient, inventory_manager_credentials, content_manager_credentials
):
    inv_headers = auth_headers(admin_token(client, inventory_manager_credentials))
    content_headers = auth_headers(admin_token(client, content_manager_credentials))
    category = create_category(client, content_headers)
    product = create_product(client, inv_headers, category["id"])

    response = client.post(
        f"/api/v1/admin/products/{product['id']}/images",
        headers=inv_headers,
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
