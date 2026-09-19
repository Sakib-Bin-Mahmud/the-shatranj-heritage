import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDPrimaryKeyMixin


class Inventory(UUIDPrimaryKeyMixin, Base):
    """One row per product variant, per ERD §5.9. `quantity_available`
    is deliberately not a stored column (computed as
    `quantity_on_hand - quantity_reserved` at query time) to avoid drift.
    """

    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_quantity_on_hand_non_negative"),
        CheckConstraint(
            "quantity_reserved >= 0", name="ck_inventory_quantity_reserved_non_negative"
        ),
    )

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    reorder_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    variant = relationship("ProductVariant")


class InventoryTransaction(UUIDPrimaryKeyMixin, Base):
    """Append-only stock movement ledger, per ERD §5.10.
    `inventory.quantity_on_hand` is reconciled against the sum of this
    table's `quantity_delta`, satisfying NFR-AUD-001 traceability.
    """

    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('restock', 'sale', 'return', 'damage', 'adjustment')",
            name="ck_inventory_transactions_change_type",
        ),
        # Every read of this table filters by variant then sorts by
        # created_at (stock history, low-stock/slow-moving reporting) —
        # a composite index serves that directly and, since
        # product_variant_id leads it, still serves a plain
        # variant-only filter (leftmost-prefix rule), so no separate
        # single-column index is needed alongside it.
        Index("ix_inventory_transactions_variant_created_at", "product_variant_id", "created_at"),
    )

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
