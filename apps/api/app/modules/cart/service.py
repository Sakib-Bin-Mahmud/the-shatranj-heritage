import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.responses import AppError
from app.modules.cart.models import Cart, CartItem
from app.modules.catalog.models import Product, ProductVariant
from app.modules.catalog.service import effective_price, quantity_available
from app.modules.inventory.models import Inventory

# --- Inventory helpers -----------------------------------------------------


async def _inventory_by_variant_ids(
    session: AsyncSession, variant_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Inventory]:
    if not variant_ids:
        return {}
    rows = await session.scalars(
        select(Inventory).where(Inventory.product_variant_id.in_(variant_ids))
    )
    return {row.product_variant_id: row for row in rows}


async def _get_inventory(session: AsyncSession, product_variant_id: uuid.UUID) -> Inventory | None:
    return await session.scalar(
        select(Inventory).where(Inventory.product_variant_id == product_variant_id)
    )


async def _get_active_variant_or_404(
    session: AsyncSession, product_variant_id: uuid.UUID
) -> ProductVariant:
    """US-CRT-001: "Available products can be added" — a variant whose
    product is draft/archived, or that is itself archived, is treated
    the same as nonexistent (matches the catalog module's public
    visibility rule).
    """
    variant = await session.scalar(
        select(ProductVariant)
        .options(selectinload(ProductVariant.product))
        .where(ProductVariant.id == product_variant_id)
    )
    if not variant or variant.status != "active" or variant.product.status != "active":
        raise AppError(status_code=404, code="NOT_FOUND", message="Product variant not found.")
    return variant


# --- Cart lookup / creation --------------------------------------------------


async def get_or_create_cart(
    session: AsyncSession, *, customer_id: uuid.UUID | None = None, session_id: str | None = None
) -> Cart:
    if customer_id:
        query = select(Cart).where(Cart.customer_id == customer_id, Cart.status == "active")
    else:
        query = select(Cart).where(Cart.session_id == session_id, Cart.status == "active")

    cart = await session.scalar(query.options(selectinload(Cart.items)))
    if cart:
        return cart

    cart = Cart(customer_id=customer_id, session_id=None if customer_id else session_id)
    session.add(cart)
    await session.flush()
    # A brand-new cart has no items, but leaving the `items` collection
    # untouched here means the ORM treats it as *unloaded* — the next
    # plain `cart.items` access would try an implicit lazy SELECT,
    # which raises MissingGreenlet in async SQLAlchemy (the same
    # Phase 2 pitfall documented for build_category_tree). Explicitly
    # (and awaited-ly) loading it here avoids that; assigning `[]`
    # directly doesn't work either since even that triggers an
    # unawaited lazy load of the "old" collection value first.
    await session.refresh(cart, attribute_names=["items"])
    return cart


async def get_cart_by_id(session: AsyncSession, cart_id: uuid.UUID) -> Cart:
    """Re-fetches a cart with a fresh, fully-populated `items` collection.
    Used after a mutation + commit instead of reusing the in-memory
    `Cart` object passed into a service call, whose `items` collection
    can go stale (e.g. a new item added via `add_item` isn't appended
    to `cart.items` in memory).

    A plain `select(...).options(selectinload(Cart.items))` is NOT
    enough here: `cart` is already in the session's identity map (it's
    the same object `get_or_create_cart` returned earlier in this
    request), and SQLAlchemy skips re-populating an already-loaded
    collection unless the query uses `populate_existing()` — so the
    stale, empty `items` from before would silently survive the
    "fresh" query. `session.refresh()` forces the reload instead.
    """
    cart = await session.get(Cart, cart_id)
    if not cart:
        raise AppError(status_code=404, code="NOT_FOUND", message="Cart not found.")
    await session.refresh(cart, attribute_names=["items"])
    return cart


async def get_item_or_404(session: AsyncSession, cart: Cart, item_id: uuid.UUID) -> CartItem:
    item = await session.get(CartItem, item_id)
    if not item or item.cart_id != cart.id:
        raise AppError(status_code=404, code="NOT_FOUND", message="Cart item not found.")
    return item


# --- Mutations ---------------------------------------------------------


async def _add_or_increment(
    session: AsyncSession,
    cart: Cart,
    *,
    product_variant_id: uuid.UUID,
    quantity: int,
    cap_to_available: bool = False,
) -> CartItem | None:
    """Shared by `add_item` (raises on insufficient stock) and cart
    merging on login (silently caps instead — a login must never fail
    because a guest cart item went out of stock in the meantime).
    """
    variant = await _get_active_variant_or_404(session, product_variant_id)
    available = quantity_available(await _get_inventory(session, product_variant_id))

    existing = await session.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.product_variant_id == product_variant_id
        )
    )
    desired_quantity = quantity + (existing.quantity if existing else 0)

    if desired_quantity > available:
        if not cap_to_available:
            raise AppError(
                status_code=422,
                code="INSUFFICIENT_STOCK",
                message=f"Only {available} unit(s) available.",
            )
        desired_quantity = available

    if desired_quantity <= 0:
        return None

    price = effective_price(variant, variant.product)
    if existing:
        existing.quantity = desired_quantity
        existing.unit_price_snapshot = price
        item = existing
    else:
        item = CartItem(
            cart_id=cart.id,
            product_variant_id=product_variant_id,
            quantity=desired_quantity,
            unit_price_snapshot=price,
        )
        session.add(item)

    await session.flush()
    return item


async def add_item(
    session: AsyncSession, cart: Cart, *, product_variant_id: uuid.UUID, quantity: int = 1
) -> CartItem:
    item = await _add_or_increment(
        session, cart, product_variant_id=product_variant_id, quantity=quantity
    )
    assert item is not None  # quantity is validated > 0 by the request schema
    return item


async def update_item_quantity(
    session: AsyncSession, cart: Cart, item_id: uuid.UUID, quantity: int
) -> CartItem:
    item = await get_item_or_404(session, cart, item_id)
    available = quantity_available(await _get_inventory(session, item.product_variant_id))
    if quantity > available:
        raise AppError(
            status_code=422,
            code="INSUFFICIENT_STOCK",
            message=f"Only {available} unit(s) available.",
        )
    item.quantity = quantity
    await session.flush()
    return item


async def remove_item(session: AsyncSession, cart: Cart, item_id: uuid.UUID) -> None:
    item = await get_item_or_404(session, cart, item_id)
    await session.delete(item)
    await session.flush()


async def merge_guest_cart_into_customer(
    session: AsyncSession, *, customer_id: uuid.UUID, session_id: str | None
) -> Cart:
    """Called right after login/registration (US-CRT-008's MVP slice):
    an active guest cart identified by the `cart_session_id` cookie is
    folded into the customer's own cart, capping any item at current
    availability rather than failing the login.
    """
    customer_cart = await get_or_create_cart(session, customer_id=customer_id)
    if not session_id:
        return customer_cart

    guest_cart = await session.scalar(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.session_id == session_id, Cart.customer_id.is_(None), Cart.status == "active")
    )
    if not guest_cart:
        return customer_cart

    for guest_item in list(guest_cart.items):
        try:
            await _add_or_increment(
                session,
                customer_cart,
                product_variant_id=guest_item.product_variant_id,
                quantity=guest_item.quantity,
                cap_to_available=True,
            )
        except AppError:
            continue  # variant no longer exists — drop it silently on merge

    await session.delete(guest_cart)
    await session.flush()
    return customer_cart


# --- Revalidation (US-CRT-009) ----------------------------------------------


async def revalidate_cart(session: AsyncSession, cart: Cart) -> list[str]:
    """Re-checks every item against current product/variant status and
    stock, self-healing the cart (removing unavailable items, clamping
    over-quantity ones) and returning human-readable warnings. Called
    by `GET /cart` and will be the hook Checkout (Phase 6) calls before
    letting a customer proceed to payment.
    """
    if not cart.items:
        return []

    variant_ids = [item.product_variant_id for item in cart.items]
    variants = await session.scalars(
        select(ProductVariant)
        .options(selectinload(ProductVariant.product))
        .where(ProductVariant.id.in_(variant_ids))
    )
    variants_by_id = {v.id: v for v in variants}
    inventory_by_variant = await _inventory_by_variant_ids(session, variant_ids)

    warnings: list[str] = []
    for item in list(cart.items):
        variant = variants_by_id.get(item.product_variant_id)
        if not variant or variant.status != "active" or variant.product.status != "active":
            label = variant.variant_name if variant else "An item"
            warnings.append(f"{label} is no longer available and was removed from your cart.")
            cart.items.remove(item)  # cascade="all, delete-orphan" deletes it at flush
            continue

        available = quantity_available(inventory_by_variant.get(item.product_variant_id))
        if available <= 0:
            warnings.append(
                f"{variant.variant_name} is out of stock and was removed from your cart."
            )
            cart.items.remove(item)
        elif item.quantity > available:
            item.quantity = available
            warnings.append(
                f"Quantity for {variant.variant_name} was reduced to {available} "
                "due to limited stock."
            )

    await session.flush()
    return warnings


# --- Response building -------------------------------------------------


async def build_cart_response(session: AsyncSession, cart: Cart) -> dict[str, Any]:
    items = cart.items
    variant_ids = [item.product_variant_id for item in items]

    variants = await session.scalars(
        select(ProductVariant)
        .options(selectinload(ProductVariant.product).selectinload(Product.images))
        .where(ProductVariant.id.in_(variant_ids))
    )
    variants_by_id = {v.id: v for v in variants}
    inventory_by_variant = await _inventory_by_variant_ids(session, variant_ids)

    item_dicts = []
    subtotal = Decimal("0.00")
    for item in items:
        variant = variants_by_id.get(item.product_variant_id)
        product = variant.product if variant else None
        available = quantity_available(inventory_by_variant.get(item.product_variant_id))
        line_total = item.unit_price_snapshot * item.quantity
        subtotal += line_total

        primary_image = None
        if product and product.images:
            primary_image = (
                next((img for img in product.images if img.is_primary), None) or (product.images[0])
            )

        item_dicts.append(
            {
                "id": item.id,
                "product_variant_id": item.product_variant_id,
                "product_id": product.id if product else None,
                "product_name": product.name if product else None,
                "product_slug": product.slug if product else None,
                "sku": variant.sku if variant else None,
                "variant_name": variant.variant_name if variant else None,
                "primary_image_url": primary_image.url if primary_image else None,
                "quantity": item.quantity,
                "unit_price_snapshot": item.unit_price_snapshot,
                "line_total": line_total,
                "max_available": available,
                "is_available": variant is not None and available >= item.quantity,
            }
        )

    # Phase 4 builds this as the standalone pricing service Checkout
    # (Phase 6) reuses unchanged; shipping/tax are real placeholders
    # (not yet wired to a rate/tax engine) and discount stays additive
    # so V2's coupon engine only needs to set it, not change the shape.
    estimated_shipping = Decimal("0.00")
    estimated_tax = Decimal("0.00")
    discount_amount = Decimal("0.00")
    total = subtotal + estimated_shipping + estimated_tax - discount_amount

    return {
        "id": cart.id,
        "item_count": sum(item.quantity for item in items),
        "items": item_dicts,
        "subtotal": subtotal,
        "estimated_shipping": estimated_shipping,
        "estimated_tax": estimated_tax,
        "discount_amount": discount_amount,
        "total": total,
    }
