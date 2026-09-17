import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Guest or customer shopping cart, per ERD §5.11. A guest cart is
    identified by `session_id` (no `customer_id`); on login it is
    merged into the customer's cart (see cart/service.py) rather than
    reassigned, so a customer never has two `active` carts.
    """

    __tablename__ = "carts"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'converted', 'abandoned')", name="ck_carts_status"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )

    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.created_at"
    )


class CartItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Line item in a cart, per ERD §5.11. `unit_price_snapshot` locks
    in the variant's effective price at add-time, so a mid-cart price
    change can't silently alter what the customer sees at checkout —
    the same snapshot pattern Phase 5's order_items will reuse.
    """

    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
        UniqueConstraint("cart_id", "product_variant_id", name="uq_cart_items_cart_variant"),
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="items")
    variant = relationship("ProductVariant")
