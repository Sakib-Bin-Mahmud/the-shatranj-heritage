import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Courier assignment/tracking for an order, per ERD §5.14. Created
    here (Phase 5) so the table exists for `orders`/`payments` to
    reference conceptually, but no service/router logic populates it
    until Phase 6 (courier integration) — see docs/Implementation Plan.md.
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
