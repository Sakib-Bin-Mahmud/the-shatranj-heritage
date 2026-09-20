import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import low_stock_variants
from app.core.responses import AppError
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import Inventory, InventoryTransaction


async def refresh_low_stock_gauge(session: AsyncSession) -> int:
    """NFR-MON-002 (alerting for low stock): recomputes the count of
    variants at or below their reorder threshold and publishes it as a
    Prometheus gauge. Called periodically from the app lifespan (see
    main.py) rather than on every inventory write, since it's a
    monitoring signal, not something any request path needs read-your-
    writes consistency on.
    """
    count = (
        await session.scalar(
            select(func.count())
            .select_from(Inventory)
            .where(
                (Inventory.quantity_on_hand - Inventory.quantity_reserved)
                <= Inventory.reorder_threshold
            )
        )
        or 0
    )
    low_stock_variants.set(count)
    return count


async def get_inventory_or_404(session: AsyncSession, product_variant_id: uuid.UUID) -> Inventory:
    inventory = await session.scalar(
        select(Inventory).where(Inventory.product_variant_id == product_variant_id)
    )
    if not inventory:
        raise AppError(
            status_code=404, code="NOT_FOUND", message="No inventory record for this variant."
        )
    return inventory


async def list_inventory(
    session: AsyncSession, *, page: int, limit: int, low_stock_only: bool = False
) -> tuple[list[dict], int]:
    """US-INV-002. Joins in variant/product names so the admin list view
    doesn't need N+1 lookups."""
    query = (
        select(Inventory, ProductVariant, Product)
        .join(ProductVariant, ProductVariant.id == Inventory.product_variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
    )
    count_query = select(func.count()).select_from(Inventory)

    if low_stock_only:
        low_stock_condition = (
            Inventory.quantity_on_hand - Inventory.quantity_reserved
        ) <= Inventory.reorder_threshold
        query = query.where(low_stock_condition)
        count_query = select(func.count()).select_from(Inventory).where(low_stock_condition)

    total = await session.scalar(count_query) or 0
    rows = (
        await session.execute(
            query.order_by(Product.name, ProductVariant.variant_name)
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).all()

    items = [
        {
            "id": inventory.id,
            "product_variant_id": inventory.product_variant_id,
            "variant_sku": variant.sku,
            "variant_name": variant.variant_name,
            "product_name": product.name,
            "quantity_on_hand": inventory.quantity_on_hand,
            "quantity_reserved": inventory.quantity_reserved,
            "quantity_available": inventory.quantity_on_hand - inventory.quantity_reserved,
            "reorder_threshold": inventory.reorder_threshold,
            "is_low_stock": (inventory.quantity_on_hand - inventory.quantity_reserved)
            <= inventory.reorder_threshold,
        }
        for inventory, variant, product in rows
    ]
    return items, total


async def adjust_inventory(
    session: AsyncSession,
    *,
    product_variant_id: uuid.UUID,
    admin_id: uuid.UUID,
    change_type: str,
    quantity_delta: int,
    note: str | None,
) -> Inventory:
    """US-INV-001, BR-INV-003. Writes the ledger row and updates the
    running total in the same transaction — never edits the stock count
    directly, so every change stays traceable (NFR-AUD-001)."""
    inventory = await get_inventory_or_404(session, product_variant_id)

    new_quantity = inventory.quantity_on_hand + quantity_delta
    if new_quantity < 0:
        raise AppError(
            status_code=422,
            code="NEGATIVE_STOCK",
            message="This adjustment would take quantity_on_hand negative.",
        )

    inventory.quantity_on_hand = new_quantity
    session.add(
        InventoryTransaction(
            product_variant_id=product_variant_id,
            change_type=change_type,
            quantity_delta=quantity_delta,
            note=note,
            created_by=admin_id,
        )
    )
    await session.flush()
    return inventory


async def list_transactions(
    session: AsyncSession, product_variant_id: uuid.UUID, *, page: int, limit: int
) -> tuple[list[InventoryTransaction], int]:
    """US-INV-003."""
    await get_inventory_or_404(session, product_variant_id)

    count_query = (
        select(func.count())
        .select_from(InventoryTransaction)
        .where(InventoryTransaction.product_variant_id == product_variant_id)
    )
    total = await session.scalar(count_query) or 0

    transactions = await session.scalars(
        select(InventoryTransaction)
        .where(InventoryTransaction.product_variant_id == product_variant_id)
        .order_by(InventoryTransaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(transactions), total
