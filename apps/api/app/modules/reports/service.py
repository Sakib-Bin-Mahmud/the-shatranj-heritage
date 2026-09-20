from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import AppError
from app.modules.catalog.models import Product, ProductVariant
from app.modules.customers.models import Customer
from app.modules.inventory.models import Inventory, InventoryTransaction
from app.modules.orders.models import Order, OrderItem
from app.modules.payments.models import Refund

# Orders in these statuses represent money actually collected; `pending`/
# `awaiting_payment` haven't been paid yet and `cancelled`/`returned`/
# `refunded` no longer represent revenue the business keeps.
REVENUE_ORDER_STATUSES = ("confirmed", "packed", "shipped", "delivered")

VALID_GROUP_BY = ("day", "week", "month")


def resolve_date_range(from_date: date | None, to_date: date | None) -> tuple[date, date]:
    """Every reporting endpoint defaults to a trailing 30-day window when
    no explicit range is given."""
    resolved_to = to_date or datetime.now(UTC).date()
    resolved_from = from_date or (resolved_to - timedelta(days=30))
    return resolved_from, resolved_to


def _check_group_by(group_by: str) -> None:
    if group_by not in VALID_GROUP_BY:
        raise AppError(
            status_code=400,
            code="INVALID_GROUP_BY",
            message=f"group_by must be one of: {', '.join(VALID_GROUP_BY)}.",
        )


async def get_sales_report(session: AsyncSession, *, from_date: date, to_date: date) -> dict:
    """US-RPT-001."""
    date_filter = (func.date(Order.placed_at) >= from_date, func.date(Order.placed_at) <= to_date)

    status_rows = (
        await session.execute(
            select(Order.status, func.count()).where(*date_filter).group_by(Order.status)
        )
    ).all()
    orders_by_status = {status: count for status, count in status_rows}
    total_orders = sum(orders_by_status.values())

    total_revenue, revenue_order_count = (
        await session.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0), func.count())
            .where(*date_filter)
            .where(Order.status.in_(REVENUE_ORDER_STATUSES))
        )
    ).one()
    average_order_value = (
        (Decimal(total_revenue) / revenue_order_count) if revenue_order_count else Decimal("0.00")
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
        "orders_by_status": orders_by_status,
    }


async def get_revenue_report(
    session: AsyncSession, *, from_date: date, to_date: date, group_by: str
) -> dict:
    """FR-RPT-002."""
    _check_group_by(group_by)

    period = func.date_trunc(group_by, Order.placed_at)
    rows = (
        await session.execute(
            select(period.label("period"), func.sum(Order.total_amount), func.count())
            .where(Order.status.in_(REVENUE_ORDER_STATUSES))
            .where(func.date(Order.placed_at) >= from_date, func.date(Order.placed_at) <= to_date)
            .group_by(period)
            .order_by(period)
        )
    ).all()

    return {
        "from_date": from_date,
        "to_date": to_date,
        "group_by": group_by,
        "points": [
            {"period": period_dt.date(), "revenue": revenue, "order_count": count}
            for period_dt, revenue, count in rows
        ],
    }


async def get_inventory_report(session: AsyncSession, *, slow_moving_days: int) -> dict:
    """US-RPT-002."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=slow_moving_days)

    low_stock_rows = (
        await session.execute(
            select(Inventory, ProductVariant, Product)
            .join(ProductVariant, Inventory.product_variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                (Inventory.quantity_on_hand - Inventory.quantity_reserved)
                <= Inventory.reorder_threshold
            )
            .order_by(Inventory.quantity_on_hand - Inventory.quantity_reserved)
        )
    ).all()

    last_sale_subq = (
        select(
            InventoryTransaction.product_variant_id,
            func.max(InventoryTransaction.created_at).label("last_sale_at"),
        )
        .where(InventoryTransaction.change_type == "sale")
        .group_by(InventoryTransaction.product_variant_id)
        .subquery()
    )

    slow_moving_rows = (
        await session.execute(
            select(Inventory, ProductVariant, Product, last_sale_subq.c.last_sale_at)
            .join(ProductVariant, Inventory.product_variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .outerjoin(
                last_sale_subq, last_sale_subq.c.product_variant_id == Inventory.product_variant_id
            )
            .where(Inventory.quantity_on_hand > 0)
            .where(
                or_(
                    last_sale_subq.c.last_sale_at.is_(None),
                    last_sale_subq.c.last_sale_at < cutoff,
                )
            )
        )
    ).all()

    return {
        "low_stock": [
            {
                "product_variant_id": inv.product_variant_id,
                "sku": variant.sku,
                "variant_name": variant.variant_name,
                "product_name": product.name,
                "quantity_on_hand": inv.quantity_on_hand,
                "quantity_available": inv.quantity_on_hand - inv.quantity_reserved,
                "reorder_threshold": inv.reorder_threshold,
            }
            for inv, variant, product in low_stock_rows
        ],
        "slow_moving": [
            {
                "product_variant_id": inv.product_variant_id,
                "sku": variant.sku,
                "variant_name": variant.variant_name,
                "product_name": product.name,
                "quantity_on_hand": inv.quantity_on_hand,
                "days_since_last_sale": (now - last_sale_at).days if last_sale_at else None,
            }
            for inv, variant, product, last_sale_at in slow_moving_rows
        ],
    }


async def get_customer_report(
    session: AsyncSession, *, from_date: date, to_date: date, group_by: str
) -> dict:
    """US-RPT-003."""
    _check_group_by(group_by)

    period = func.date_trunc(group_by, Customer.created_at)
    growth_rows = (
        await session.execute(
            select(period.label("period"), func.count())
            .where(
                func.date(Customer.created_at) >= from_date,
                func.date(Customer.created_at) <= to_date,
            )
            .group_by(period)
            .order_by(period)
        )
    ).all()
    growth = [
        {"period": period_dt.date(), "new_customers": count} for period_dt, count in growth_rows
    ]
    new_customers = sum(count for _, count in growth_rows)

    total_customers = await session.scalar(select(func.count()).select_from(Customer)) or 0

    order_counts_subq = (
        select(Order.customer_id, func.count().label("order_count"))
        .where(Order.customer_id.is_not(None))
        .group_by(Order.customer_id)
        .subquery()
    )
    customers_with_orders = (
        await session.scalar(select(func.count()).select_from(order_counts_subq)) or 0
    )
    repeat_customers = (
        await session.scalar(
            select(func.count())
            .select_from(order_counts_subq)
            .where(order_counts_subq.c.order_count > 1)
        )
        or 0
    )
    repeat_customer_rate = (
        round(repeat_customers / customers_with_orders, 4) if customers_with_orders else 0.0
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "group_by": group_by,
        "total_customers": total_customers,
        "new_customers": new_customers,
        "repeat_customer_rate": repeat_customer_rate,
        "growth": growth,
    }


async def get_top_selling_products(
    session: AsyncSession, *, from_date: date, to_date: date, limit: int
) -> list[dict]:
    """FR-RPT-005."""
    rows = (
        await session.execute(
            select(
                OrderItem.product_variant_id,
                OrderItem.sku_snapshot,
                OrderItem.product_name_snapshot,
                func.sum(OrderItem.quantity).label("quantity_sold"),
                func.sum(OrderItem.line_total).label("revenue"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.status.in_(REVENUE_ORDER_STATUSES))
            .where(func.date(Order.placed_at) >= from_date, func.date(Order.placed_at) <= to_date)
            .group_by(
                OrderItem.product_variant_id,
                OrderItem.sku_snapshot,
                OrderItem.product_name_snapshot,
            )
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )
    ).all()

    return [
        {
            "product_variant_id": row.product_variant_id,
            "sku": row.sku_snapshot,
            "product_name": row.product_name_snapshot,
            "quantity_sold": int(row.quantity_sold),
            "revenue": row.revenue,
        }
        for row in rows
    ]


async def get_refund_report(session: AsyncSession, *, from_date: date, to_date: date) -> dict:
    """FR-RPT-006."""
    rows = (
        await session.execute(
            select(Refund.status, func.count(), func.coalesce(func.sum(Refund.amount), 0))
            .where(
                func.date(Refund.requested_at) >= from_date,
                func.date(Refund.requested_at) <= to_date,
            )
            .group_by(Refund.status)
        )
    ).all()

    by_status = [
        {"status": status, "count": count, "amount": amount} for status, count, amount in rows
    ]
    total_refunds = sum(row["count"] for row in by_status)
    total_refund_amount = sum((row["amount"] for row in by_status), Decimal("0.00"))

    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_refunds": total_refunds,
        "total_refund_amount": total_refund_amount,
        "by_status": by_status,
    }
