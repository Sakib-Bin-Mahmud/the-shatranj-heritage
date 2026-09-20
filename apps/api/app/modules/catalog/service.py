import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.responses import AppError
from app.modules.catalog.models import Artisan, Category, Product, ProductImage, ProductVariant
from app.modules.catalog.schemas import (
    CreateArtisanRequest,
    CreateCategoryRequest,
    CreateProductRequest,
    CreateVariantRequest,
    UpdateArtisanRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)
from app.modules.inventory.models import Inventory

# --- Categories --------------------------------------------------------


async def _check_slug_available(
    session: AsyncSession, slug: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Category).where(Category.slug == slug)
    if exclude_id:
        query = query.where(Category.id != exclude_id)
    if await session.scalar(query):
        raise AppError(
            status_code=409, code="SLUG_ALREADY_EXISTS", message="Slug is already in use."
        )


async def get_category_or_404(session: AsyncSession, category_id: uuid.UUID) -> Category:
    category = await session.get(Category, category_id)
    if not category:
        raise AppError(status_code=404, code="NOT_FOUND", message="Category not found.")
    return category


async def get_category_by_slug_or_404(session: AsyncSession, slug: str) -> Category:
    category = await session.scalar(select(Category).where(Category.slug == slug))
    if not category:
        raise AppError(status_code=404, code="NOT_FOUND", message="Category not found.")
    return category


async def create_category(session: AsyncSession, data: CreateCategoryRequest) -> Category:
    await _check_slug_available(session, data.slug)
    if data.parent_category_id:
        await get_category_or_404(session, data.parent_category_id)

    category = Category(**data.model_dump())
    session.add(category)
    await session.flush()
    return category


async def update_category(
    session: AsyncSession, category_id: uuid.UUID, data: UpdateCategoryRequest
) -> Category:
    category = await get_category_or_404(session, category_id)
    updates = data.model_dump(exclude_unset=True)

    if "slug" in updates and updates["slug"] != category.slug:
        await _check_slug_available(session, updates["slug"], exclude_id=category_id)
    if updates.get("parent_category_id"):
        if updates["parent_category_id"] == category_id:
            raise AppError(
                status_code=422,
                code="INVALID_PARENT",
                message="A category cannot be its own parent.",
            )
        await get_category_or_404(session, updates["parent_category_id"])

    for field, value in updates.items():
        setattr(category, field, value)
    await session.flush()
    return category


async def deactivate_category(session: AsyncSession, category_id: uuid.UUID) -> Category:
    category = await get_category_or_404(session, category_id)
    category.is_active = False
    await session.flush()
    return category


async def list_categories(
    session: AsyncSession, *, include_inactive: bool = False
) -> list[Category]:
    query = select(Category).order_by(Category.sort_order, Category.name)
    if not include_inactive:
        query = query.where(Category.is_active.is_(True))
    return list(await session.scalars(query))


def build_category_tree(categories: list[Category]) -> list[dict[str, Any]]:
    """Builds a plain-dict tree (not via the ORM `children`/`parent`
    relationships, which are lazy and would need a sync context to load
    — see MissingGreenlet). Each node's shape matches `CategoryResponse`
    plus a `children` list, so `CategoryTreeResponse.model_validate()`
    accepts it directly.
    """

    def to_node(category: Category) -> dict[str, Any]:
        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "image_url": category.image_url,
            "sort_order": category.sort_order,
            "parent_category_id": category.parent_category_id,
            "is_active": category.is_active,
            "children": [],
        }

    nodes_by_id = {c.id: to_node(c) for c in categories}
    roots: list[dict[str, Any]] = []

    for category in categories:
        node = nodes_by_id[category.id]
        if category.parent_category_id and category.parent_category_id in nodes_by_id:
            nodes_by_id[category.parent_category_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


# --- Artisans ------------------------------------------------------------


async def get_artisan_or_404(session: AsyncSession, artisan_id: uuid.UUID) -> Artisan:
    artisan = await session.get(Artisan, artisan_id)
    if not artisan:
        raise AppError(status_code=404, code="NOT_FOUND", message="Artisan not found.")
    return artisan


async def create_artisan(session: AsyncSession, data: CreateArtisanRequest) -> Artisan:
    artisan = Artisan(**data.model_dump())
    session.add(artisan)
    await session.flush()
    return artisan


async def update_artisan(
    session: AsyncSession, artisan_id: uuid.UUID, data: UpdateArtisanRequest
) -> Artisan:
    artisan = await get_artisan_or_404(session, artisan_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(artisan, field, value)
    await session.flush()
    return artisan


async def list_artisans(session: AsyncSession) -> list[Artisan]:
    return list(await session.scalars(select(Artisan).order_by(Artisan.name)))


# --- Pricing / stock helpers ---------------------------------------------


def effective_price(variant: ProductVariant, product: Product) -> Decimal:
    return variant.price_override if variant.price_override is not None else product.base_price


# Phase 6: neither the variant nor the product is required to record a
# weight (both fields are optional, per Phase 2), but shipping cost
# calculation needs a number for every line item — this is the
# fallback for "we don't actually know," not a claim that it's typical.
DEFAULT_ITEM_WEIGHT_GRAMS = 500


def effective_weight(variant: ProductVariant, product: Product) -> int:
    if variant.weight_grams is not None:
        return variant.weight_grams
    if product.weight_grams is not None:
        return product.weight_grams
    return DEFAULT_ITEM_WEIGHT_GRAMS


def quantity_available(inventory: Inventory | None) -> int:
    if not inventory:
        return 0
    return inventory.quantity_on_hand - inventory.quantity_reserved


def variant_stock_status(inventory: Inventory | None) -> str:
    available = quantity_available(inventory)
    if available <= 0:
        return "out_of_stock"
    if inventory and available <= inventory.reorder_threshold:
        return "low_stock"
    return "in_stock"


def product_display_price(product: Product) -> Decimal:
    active_variants = [v for v in product.variants if v.status == "active"]
    if not active_variants:
        return product.base_price
    return min(effective_price(v, product) for v in active_variants)


def product_stock_status(product: Product, inventory_by_variant: dict[uuid.UUID, Inventory]) -> str:
    active_variants = [v for v in product.variants if v.status == "active"]
    if not active_variants:
        return "out_of_stock"

    total_available = 0
    any_low = False
    for variant in active_variants:
        inventory = inventory_by_variant.get(variant.id)
        available = quantity_available(inventory)
        total_available += available
        if inventory and 0 < available <= inventory.reorder_threshold:
            any_low = True

    if total_available <= 0:
        return "out_of_stock"
    return "low_stock" if any_low else "in_stock"


async def _inventory_by_variant_ids(
    session: AsyncSession, variant_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Inventory]:
    if not variant_ids:
        return {}
    rows = await session.scalars(
        select(Inventory).where(Inventory.product_variant_id.in_(variant_ids))
    )
    return {row.product_variant_id: row for row in rows}


# --- Products --------------------------------------------------------------

PRODUCT_LOAD_OPTIONS = (
    selectinload(Product.variants),
    selectinload(Product.images),
    selectinload(Product.category),
    selectinload(Product.artisan),
)


async def _check_sku_available(
    session: AsyncSession, sku: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Product).where(Product.sku == sku)
    if exclude_id:
        query = query.where(Product.id != exclude_id)
    if await session.scalar(query):
        raise AppError(status_code=409, code="SKU_ALREADY_EXISTS", message="SKU is already in use.")


async def _check_product_slug_available(
    session: AsyncSession, slug: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Product).where(Product.slug == slug)
    if exclude_id:
        query = query.where(Product.id != exclude_id)
    if await session.scalar(query):
        raise AppError(
            status_code=409, code="SLUG_ALREADY_EXISTS", message="Slug is already in use."
        )


async def get_product_or_404(session: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await session.scalar(
        select(Product).options(*PRODUCT_LOAD_OPTIONS).where(Product.id == product_id)
    )
    if not product:
        raise AppError(status_code=404, code="NOT_FOUND", message="Product not found.")
    return product


async def get_public_product_by_slug_or_404(session: AsyncSession, slug: str) -> Product:
    product = await session.scalar(
        select(Product)
        .options(*PRODUCT_LOAD_OPTIONS)
        .where(Product.slug == slug, Product.status == "active")
    )
    if not product:
        raise AppError(status_code=404, code="NOT_FOUND", message="Product not found.")
    return product


async def create_product(session: AsyncSession, data: CreateProductRequest) -> Product:
    await _check_sku_available(session, data.sku)
    await _check_product_slug_available(session, data.slug)
    await get_category_or_404(session, data.category_id)
    if data.artisan_id:
        await get_artisan_or_404(session, data.artisan_id)

    product = Product(**data.model_dump())
    session.add(product)
    await session.flush()
    return await get_product_or_404(session, product.id)


async def update_product(
    session: AsyncSession, product_id: uuid.UUID, data: UpdateProductRequest
) -> Product:
    product = await get_product_or_404(session, product_id)
    updates = data.model_dump(exclude_unset=True)

    if "sku" in updates and updates["sku"] != product.sku:
        await _check_sku_available(session, updates["sku"], exclude_id=product_id)
    if "slug" in updates and updates["slug"] != product.slug:
        await _check_product_slug_available(session, updates["slug"], exclude_id=product_id)
    if updates.get("category_id"):
        await get_category_or_404(session, updates["category_id"])
    if updates.get("artisan_id"):
        await get_artisan_or_404(session, updates["artisan_id"])

    for field, value in updates.items():
        setattr(product, field, value)
    await session.flush()
    return product


async def archive_product(session: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await get_product_or_404(session, product_id)
    product.status = "archived"
    await session.flush()
    return product


def _variant_in_stock_subquery():
    return exists().where(
        and_(
            ProductVariant.product_id == Product.id,
            ProductVariant.status == "active",
            Inventory.product_variant_id == ProductVariant.id,
            (Inventory.quantity_on_hand - Inventory.quantity_reserved) > 0,
        )
    )


async def public_list_products(
    session: AsyncSession,
    *,
    page: int,
    limit: int,
    q: str | None = None,
    category_slug: str | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    material: str | None = None,
    availability: str = "all",
    featured: bool | None = None,
    sort: str | None = None,
) -> tuple[list[Product], int]:
    query = select(Product).where(Product.status == "active")
    count_query = select(func.count(func.distinct(Product.id))).where(Product.status == "active")

    text_query = func.websearch_to_tsquery("english", q) if q else None
    if q:
        # FR-SCH-001: relevance-ranked full-text search over name +
        # description (Product.search_vector, a GIN-indexed generated
        # column — see the model), OR'd with a SKU match per the
        # acceptance criteria in US-SRC-001 ("Search by: Product name,
        # SKU, Category, Description").
        condition = or_(Product.search_vector.op("@@")(text_query), Product.sku.ilike(f"%{q}%"))
        query = query.where(condition)
        count_query = count_query.where(condition)

    if category_slug:
        category = await session.scalar(select(Category).where(Category.slug == category_slug))
        if not category:
            return [], 0
        query = query.where(Product.category_id == category.id)
        count_query = count_query.where(Product.category_id == category.id)

    if price_min is not None:
        query = query.where(Product.base_price >= price_min)
        count_query = count_query.where(Product.base_price >= price_min)
    if price_max is not None:
        query = query.where(Product.base_price <= price_max)
        count_query = count_query.where(Product.base_price <= price_max)

    if material:
        condition = exists().where(
            and_(
                ProductVariant.product_id == Product.id,
                ProductVariant.attributes["material"].astext.ilike(f"%{material}%"),
            )
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if availability == "in_stock":
        condition = _variant_in_stock_subquery()
        query = query.where(condition)
        count_query = count_query.where(condition)

    if featured is not None:
        query = query.where(Product.is_featured.is_(featured))
        count_query = count_query.where(Product.is_featured.is_(featured))

    # Default to relevance ranking for a keyword search (unless the
    # caller explicitly asked for a different order); newest otherwise.
    effective_sort = sort or ("relevance" if q else "newest")
    sort_map = {
        "price_asc": Product.base_price.asc(),
        "price_desc": Product.base_price.desc(),
        "alphabetical": Product.name.asc(),
        "newest": Product.created_at.desc(),
        # best_selling/rating need aggregated order/review data that
        # doesn't exist yet (Phase 5/V2) — fall back to newest rather
        # than reject an otherwise-valid, spec-listed sort value.
        "best_selling": Product.created_at.desc(),
        "rating": Product.created_at.desc(),
    }
    if effective_sort == "relevance" and text_query is not None:
        query = query.order_by(func.ts_rank(Product.search_vector, text_query).desc())
    else:
        query = query.order_by(sort_map.get(effective_sort, Product.created_at.desc()))

    total = await session.scalar(count_query) or 0
    products = await session.scalars(
        query.options(*PRODUCT_LOAD_OPTIONS).offset((page - 1) * limit).limit(limit)
    )
    return list(products), total


async def search_suggestions(session: AsyncSession, *, limit: int = 6) -> dict[str, Any]:
    """US-SRC-005: offered alongside an empty search result so the
    visitor isn't left at a dead end."""
    categories = await list_categories(session)
    featured_products = list(
        await session.scalars(
            select(Product)
            .options(*PRODUCT_LOAD_OPTIONS)
            .where(Product.status == "active", Product.is_featured.is_(True))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
    )
    return {
        "categories": categories[:limit],
        "featured_products": await build_product_summaries(session, featured_products),
    }


async def admin_list_products(
    session: AsyncSession, *, page: int, limit: int, status: str | None, search: str | None
) -> tuple[list[Product], int]:
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if status:
        query = query.where(Product.status == status)
        count_query = count_query.where(Product.status == status)
    if search:
        pattern = f"%{search}%"
        condition = or_(Product.name.ilike(pattern), Product.sku.ilike(pattern))
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = await session.scalar(count_query) or 0
    products = await session.scalars(
        query.options(*PRODUCT_LOAD_OPTIONS)
        .order_by(Product.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(products), total


async def related_products(
    session: AsyncSession, product: Product, *, limit: int = 8
) -> list[Product]:
    return list(
        await session.scalars(
            select(Product)
            .options(*PRODUCT_LOAD_OPTIONS)
            .where(
                Product.category_id == product.category_id,
                Product.id != product.id,
                Product.status == "active",
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
    )


async def build_product_summaries(
    session: AsyncSession, products: list[Product]
) -> list[dict[str, Any]]:
    variant_ids = [v.id for p in products for v in p.variants]
    inventory_by_variant = await _inventory_by_variant_ids(session, variant_ids)

    summaries = []
    for product in products:
        primary_image = next((img for img in product.images if img.is_primary), None)
        if not primary_image and product.images:
            primary_image = product.images[0]
        summaries.append(
            {
                "id": product.id,
                "slug": product.slug,
                "name": product.name,
                "primary_image_url": primary_image.url if primary_image else None,
                "price": product_display_price(product),
                "stock_status": product_stock_status(product, inventory_by_variant),
                "is_featured": product.is_featured,
            }
        )
    return summaries


async def build_variant_responses(session: AsyncSession, product: Product) -> list[dict[str, Any]]:
    variant_ids = [v.id for v in product.variants]
    inventory_by_variant = await _inventory_by_variant_ids(session, variant_ids)

    return [
        {
            "id": v.id,
            "product_id": v.product_id,
            "sku": v.sku,
            "variant_name": v.variant_name,
            "price_override": v.price_override,
            "weight_grams": v.weight_grams,
            "attributes": v.attributes,
            "is_default": v.is_default,
            "status": v.status,
            "effective_price": effective_price(v, product),
            "quantity_available": quantity_available(inventory_by_variant.get(v.id)),
        }
        for v in product.variants
    ]


# --- Variants --------------------------------------------------------------


async def _check_variant_sku_available(
    session: AsyncSession, sku: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(ProductVariant).where(ProductVariant.sku == sku)
    if exclude_id:
        query = query.where(ProductVariant.id != exclude_id)
    if await session.scalar(query):
        raise AppError(
            status_code=409, code="SKU_ALREADY_EXISTS", message="Variant SKU is already in use."
        )


async def get_variant_or_404(
    session: AsyncSession, product_id: uuid.UUID, variant_id: uuid.UUID
) -> ProductVariant:
    variant = await session.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise AppError(status_code=404, code="NOT_FOUND", message="Variant not found.")
    return variant


async def _unset_other_default_variants(
    session: AsyncSession, product_id: uuid.UUID, except_id: uuid.UUID
) -> None:
    variants = await session.scalars(
        select(ProductVariant).where(
            ProductVariant.product_id == product_id, ProductVariant.id != except_id
        )
    )
    for variant in variants:
        variant.is_default = False


async def create_variant(
    session: AsyncSession, product_id: uuid.UUID, data: CreateVariantRequest
) -> ProductVariant:
    product = await get_product_or_404(session, product_id)
    await _check_variant_sku_available(session, data.sku)

    make_default = data.is_default or not product.variants

    variant = ProductVariant(
        product_id=product_id, **data.model_dump(exclude={"is_default"}), is_default=make_default
    )
    session.add(variant)
    await session.flush()

    session.add(Inventory(product_variant_id=variant.id))
    await session.flush()

    if make_default:
        await _unset_other_default_variants(session, product_id, except_id=variant.id)

    return variant


async def update_variant(
    session: AsyncSession, product_id: uuid.UUID, variant_id: uuid.UUID, data: UpdateVariantRequest
) -> ProductVariant:
    variant = await get_variant_or_404(session, product_id, variant_id)
    updates = data.model_dump(exclude_unset=True, exclude={"is_default"})
    for field, value in updates.items():
        setattr(variant, field, value)

    if data.is_default is True:
        variant.is_default = True
        await _unset_other_default_variants(session, product_id, except_id=variant_id)
    elif data.is_default is False:
        variant.is_default = False

    await session.flush()
    return variant


async def archive_variant(
    session: AsyncSession, product_id: uuid.UUID, variant_id: uuid.UUID
) -> ProductVariant:
    variant = await get_variant_or_404(session, product_id, variant_id)
    variant.status = "archived"
    await session.flush()
    return variant


# --- Images ----------------------------------------------------------------


async def _unset_other_primary_images(
    session: AsyncSession, product_id: uuid.UUID, except_id: uuid.UUID
) -> None:
    images = await session.scalars(
        select(ProductImage).where(
            ProductImage.product_id == product_id, ProductImage.id != except_id
        )
    )
    for image in images:
        image.is_primary = False


async def add_image(
    session: AsyncSession,
    product_id: uuid.UUID,
    *,
    url: str,
    alt_text: str | None,
    is_primary: bool,
    product_variant_id: uuid.UUID | None,
) -> ProductImage:
    product = await get_product_or_404(session, product_id)
    if product_variant_id:
        await get_variant_or_404(session, product_id, product_variant_id)

    make_primary = is_primary or not product.images

    image = ProductImage(
        product_id=product_id,
        product_variant_id=product_variant_id,
        url=url,
        alt_text=alt_text,
        is_primary=make_primary,
    )
    session.add(image)
    await session.flush()

    if make_primary:
        await _unset_other_primary_images(session, product_id, except_id=image.id)

    return image


async def get_image_or_404(
    session: AsyncSession, product_id: uuid.UUID, image_id: uuid.UUID
) -> ProductImage:
    image = await session.get(ProductImage, image_id)
    if not image or image.product_id != product_id:
        raise AppError(status_code=404, code="NOT_FOUND", message="Image not found.")
    return image


async def delete_image(session: AsyncSession, product_id: uuid.UUID, image_id: uuid.UUID) -> str:
    image = await get_image_or_404(session, product_id, image_id)
    url = image.url
    was_primary = image.is_primary
    await session.delete(image)
    await session.flush()

    if was_primary:
        remaining = await session.scalars(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order)
        )
        first = next(iter(remaining), None)
        if first:
            first.is_primary = True

    return url
