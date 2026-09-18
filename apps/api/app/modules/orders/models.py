import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

# BR-ORD-003 lifecycle. "pending" is transient in practice — an order
# is flipped to "awaiting_payment" within the same transaction that
# creates it (see orders/service.py:place_order) — but stays a valid,
# checkable value since nothing prevents observing it mid-transaction
# or in a future flow that pauses there.
ORDER_STATUSES = (
    "pending",
    "awaiting_payment",
    "confirmed",
    "packed",
    "shipped",
    "delivered",
    "cancelled",
    "returned",
    "refunded",
)


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Placed order, per ERD §5.12. `customer_id` is nullable for guest
    checkout (US-AUTH-004); guest orders carry `guest_email`/
    `guest_phone` instead. Address snapshots are copied JSONB, not FKs,
    so a later address-book edit can never retroactively change what an
    already-placed order says it shipped to.
    """

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(f"status IN {ORDER_STATUSES}", name="ck_orders_status"),
        CheckConstraint(
            "customer_id IS NOT NULL OR guest_email IS NOT NULL OR guest_phone IS NOT NULL",
            name="ck_orders_customer_or_guest_contact",
        ),
    )

    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default="BDT"
    )
    shipping_address_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    billing_address_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # NFR-REL-001 ("each successful order shall be created exactly
    # once"): not part of the ERD's literal column list, but required
    # to make POST /orders' Idempotency-Key header actually enforceable
    # — a client-generated token, unique when present, checked before
    # insert and relied on again (via its DB-level uniqueness) to
    # survive a genuine race between two retries of the same request.
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.created_at"
    )


class OrderItem(UUIDPrimaryKeyMixin, Base):
    """Order line item, per ERD §5.12. Snapshots product name/SKU/price
    at order time so the order remains an accurate historical record
    even if the product is later renamed, re-priced, or archived.
    """

    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),)

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    product_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    order: Mapped[Order] = relationship(back_populates="items")
