import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.core.storage import delete_image_url, upload_image_file
from app.modules.auth.dependencies import require_permission
from app.modules.catalog import service as catalog_service
from app.modules.catalog.models import Product
from app.modules.catalog.schemas import (
    ArtisanResponse,
    CategoryResponse,
    CategoryTreeResponse,
    CreateArtisanRequest,
    CreateCategoryRequest,
    CreateProductRequest,
    CreateVariantRequest,
    ImageResponse,
    ProductDetail,
    UpdateArtisanRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)

router = APIRouter(tags=["Catalog"])
admin_router = APIRouter(prefix="/admin", tags=["Admin - Catalog"])


async def _product_detail(session: AsyncSession, product: Product) -> dict:
    return ProductDetail(
        id=product.id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        description=product.description,
        category=CategoryResponse.model_validate(product.category),
        artisan=ArtisanResponse.model_validate(product.artisan) if product.artisan else None,
        brand=product.brand,
        base_price=product.base_price,
        currency=product.currency,
        weight_grams=product.weight_grams,
        status=product.status,
        is_featured=product.is_featured,
        variants=await catalog_service.build_variant_responses(session, product),
        images=[ImageResponse.model_validate(i) for i in product.images],
    ).model_dump()


# --- Public: categories -----------------------------------------------


@router.get("/categories")
async def list_categories(session: AsyncSession = Depends(get_db_session)) -> dict:
    """US-CAT-003."""
    categories = await catalog_service.list_categories(session)
    tree = catalog_service.build_category_tree(categories)
    return success_envelope(
        data=[CategoryTreeResponse.model_validate(c).model_dump() for c in tree]
    )


@router.get("/categories/{slug}")
async def get_category(slug: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    """US-CAT-003."""
    category = await catalog_service.get_category_by_slug_or_404(session, slug)
    return success_envelope(data=CategoryResponse.model_validate(category).model_dump())


# --- Public: products ----------------------------------------------------


@router.get("/products")
async def list_products(
    q: str | None = None,
    category: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    material: str | None = None,
    availability: str = Query(default="all", pattern="^(in_stock|all)$"),
    featured: bool | None = None,
    sort: str | None = Query(
        default=None,
        pattern="^(relevance|price_asc|price_desc|newest|best_selling|rating|alphabetical)$",
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-SCH-001…007, US-SRC-001…003. `sort` defaults to relevance
    ranking when `q` is given, newest otherwise (see
    catalog/service.py:public_list_products)."""
    products, total = await catalog_service.public_list_products(
        session,
        page=page,
        limit=limit,
        q=q,
        category_slug=category,
        price_min=price_min,
        price_max=price_max,
        material=material,
        availability=availability,
        featured=featured,
        sort=sort,
    )
    summaries = await catalog_service.build_product_summaries(session, products)
    total_pages = (total + limit - 1) // limit if total else 0

    data = {
        "items": summaries,
        "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
    }
    if q and total == 0:
        # US-SRC-005: helpful feedback instead of a dead end.
        suggestions = await catalog_service.search_suggestions(session)
        data["suggestions"] = {
            "categories": [
                CategoryResponse.model_validate(c).model_dump() for c in suggestions["categories"]
            ],
            "featured_products": suggestions["featured_products"],
        }

    return success_envelope(data=data)


@router.get("/products/{slug}")
async def get_product(slug: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    """US-CAT-002."""
    product = await catalog_service.get_public_product_by_slug_or_404(session, slug)
    return success_envelope(data=await _product_detail(session, product))


@router.get("/products/{product_id}/related")
async def get_related_products(
    product_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """US-CAT-006."""
    product = await catalog_service.get_product_or_404(session, product_id)
    related = await catalog_service.related_products(session, product)
    summaries = await catalog_service.build_product_summaries(session, related)
    return success_envelope(data=summaries)


# --- Admin: categories (Content permission) -----------------------------


@admin_router.get("/categories", dependencies=[Depends(require_permission("categories.write"))])
async def admin_list_categories(session: AsyncSession = Depends(get_db_session)) -> dict:
    categories = await catalog_service.list_categories(session, include_inactive=True)
    return success_envelope(
        data=[CategoryResponse.model_validate(c).model_dump() for c in categories]
    )


@admin_router.post(
    "/categories", status_code=201, dependencies=[Depends(require_permission("categories.write"))]
)
async def admin_create_category(
    payload: CreateCategoryRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-ADM-001."""
    category = await catalog_service.create_category(session, payload)
    await session.commit()
    return success_envelope(data=CategoryResponse.model_validate(category).model_dump())


@admin_router.patch(
    "/categories/{category_id}", dependencies=[Depends(require_permission("categories.write"))]
)
async def admin_update_category(
    category_id: uuid.UUID,
    payload: UpdateCategoryRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-ADM-001."""
    category = await catalog_service.update_category(session, category_id, payload)
    await session.commit()
    return success_envelope(data=CategoryResponse.model_validate(category).model_dump())


@admin_router.delete(
    "/categories/{category_id}", dependencies=[Depends(require_permission("categories.write"))]
)
async def admin_deactivate_category(
    category_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-ADM-001. Deactivates rather than hard-deletes: categories are
    referenced by products with `ON DELETE RESTRICT`, and a hard delete
    would fail at the database level anyway once any product uses it."""
    category = await catalog_service.deactivate_category(session, category_id)
    await session.commit()
    return success_envelope(data=CategoryResponse.model_validate(category).model_dump())


# --- Admin: artisans (Inventory permission) -------------------------------


@admin_router.get("/artisans", dependencies=[Depends(require_permission("products.write"))])
async def admin_list_artisans(session: AsyncSession = Depends(get_db_session)) -> dict:
    artisans = await catalog_service.list_artisans(session)
    return success_envelope(data=[ArtisanResponse.model_validate(a).model_dump() for a in artisans])


@admin_router.post(
    "/artisans", status_code=201, dependencies=[Depends(require_permission("products.write"))]
)
async def admin_create_artisan(
    payload: CreateArtisanRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    artisan = await catalog_service.create_artisan(session, payload)
    await session.commit()
    return success_envelope(data=ArtisanResponse.model_validate(artisan).model_dump())


@admin_router.patch(
    "/artisans/{artisan_id}", dependencies=[Depends(require_permission("products.write"))]
)
async def admin_update_artisan(
    artisan_id: uuid.UUID,
    payload: UpdateArtisanRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    artisan = await catalog_service.update_artisan(session, artisan_id, payload)
    await session.commit()
    return success_envelope(data=ArtisanResponse.model_validate(artisan).model_dump())


# --- Admin: products (Inventory permission) -------------------------------


@admin_router.get("/products", dependencies=[Depends(require_permission("products.write"))])
async def admin_list_products(
    status: str | None = Query(default=None, pattern="^(draft|active|archived)$"),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    products, total = await catalog_service.admin_list_products(
        session, page=page, limit=limit, status=status, search=search
    )
    items = [await _product_detail(session, p) for p in products]
    total_pages = (total + limit - 1) // limit if total else 0
    return success_envelope(
        data={
            "items": items,
            "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
        }
    )


@admin_router.get(
    "/products/{product_id}", dependencies=[Depends(require_permission("products.write"))]
)
async def admin_get_product(
    product_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))


@admin_router.post(
    "/products", status_code=201, dependencies=[Depends(require_permission("products.write"))]
)
async def admin_create_product(
    payload: CreateProductRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CAT-001, BR-PRO-001."""
    product = await catalog_service.create_product(session, payload)
    await session.commit()
    return success_envelope(data=await _product_detail(session, product))


@admin_router.patch(
    "/products/{product_id}", dependencies=[Depends(require_permission("products.write"))]
)
async def admin_update_product(
    product_id: uuid.UUID,
    payload: UpdateProductRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-CAT-002."""
    product = await catalog_service.update_product(session, product_id, payload)
    await session.commit()
    return success_envelope(data=await _product_detail(session, product))


@admin_router.delete(
    "/products/{product_id}", dependencies=[Depends(require_permission("products.write"))]
)
async def admin_archive_product(
    product_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CAT-003."""
    product = await catalog_service.archive_product(session, product_id)
    await session.commit()
    return success_envelope(data=await _product_detail(session, product))


# --- Admin: variants -------------------------------------------------------


@admin_router.post(
    "/products/{product_id}/variants",
    status_code=201,
    dependencies=[Depends(require_permission("products.write"))],
)
async def admin_create_variant(
    product_id: uuid.UUID,
    payload: CreateVariantRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-CAT-005."""
    await catalog_service.create_variant(session, product_id, payload)
    await session.commit()
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))


@admin_router.patch(
    "/products/{product_id}/variants/{variant_id}",
    dependencies=[Depends(require_permission("products.write"))],
)
async def admin_update_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: UpdateVariantRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-CAT-005."""
    await catalog_service.update_variant(session, product_id, variant_id, payload)
    await session.commit()
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))


@admin_router.delete(
    "/products/{product_id}/variants/{variant_id}",
    dependencies=[Depends(require_permission("products.write"))],
)
async def admin_archive_variant(
    product_id: uuid.UUID, variant_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CAT-005. Archives rather than hard-deletes: variants are
    referenced by inventory transactions (and, from Phase 5, order
    items) that must remain intact."""
    await catalog_service.archive_variant(session, product_id, variant_id)
    await session.commit()
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))


# --- Admin: images ----------------------------------------------------------


@admin_router.post(
    "/products/{product_id}/images",
    status_code=201,
    dependencies=[Depends(require_permission("products.write"))],
)
async def admin_add_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    is_primary: bool = Form(default=False),
    product_variant_id: uuid.UUID | None = Form(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-CAT-004."""
    url = await upload_image_file(file, key_prefix=f"products/{product_id}")
    await catalog_service.add_image(
        session,
        product_id,
        url=url,
        alt_text=alt_text,
        is_primary=is_primary,
        product_variant_id=product_variant_id,
    )
    await session.commit()
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))


@admin_router.delete(
    "/products/{product_id}/images/{image_id}",
    dependencies=[Depends(require_permission("products.write"))],
)
async def admin_delete_image(
    product_id: uuid.UUID, image_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CAT-004."""
    url = await catalog_service.delete_image(session, product_id, image_id)
    await session.commit()
    delete_image_url(url)
    product = await catalog_service.get_product_or_404(session, product_id)
    return success_envelope(data=await _product_detail(session, product))
