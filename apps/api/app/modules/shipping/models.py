import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ShippingRate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Admin-configurable shipping cost rule, per BR-SHP-002 ("shipping
    charges shall be calculated based on configurable business rules");
    not in the ERD's literal table list, added in Phase 6 to replace
    Phase 5's flat per-method placeholder with a real location- and
    weight-based calculation. One row per (zone, method); an order's
    weight beyond `base_weight_grams` is charged at `per_kg_rate`.
    Phase 7's admin settings UI manages these rows — Phase 6 only
    reads them and ships sane defaults via migration.
    """

    __tablename__ = "shipping_rates"
    __table_args__ = (
        CheckConstraint("zone IN ('dhaka', 'outside_dhaka')", name="ck_shipping_rates_zone"),
        CheckConstraint("method IN ('standard', 'express')", name="ck_shipping_rates_method"),
        UniqueConstraint("zone", "method", name="uq_shipping_rates_zone_method"),
    )

    zone: Mapped[str] = mapped_column(String(20), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    base_weight_grams: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000, server_default="1000"
    )
    per_kg_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Courier assignment/tracking for an order, per ERD §5.14. The
    table existed from Phase 5 (so `orders`/`payments` could reference
    it conceptually); Phase 6 adds the service/router logic that
    populates it — see docs/Implementation Plan.md.
    """

    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'dispatched', 'in_transit', 'delivered', 'failed')",
            name="ck_shipments_status",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    courier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    estimated_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
