import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

PAYMENT_METHODS = ("bkash", "nagad", "rocket", "card", "cod")
PAYMENT_STATUSES = ("pending", "successful", "failed", "refunded", "cancelled")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A payment attempt against an order, per ERD §5.13. An order can
    have more than one row here — a retried online-payment attempt
    (US-PAY-003) creates a new one rather than overwriting the failed
    attempt, preserving the full attempt history.
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(f"method IN {PAYMENT_METHODS}", name="ck_payments_method"),
        CheckConstraint(f"status IN {PAYMENT_STATUSES}", name="ck_payments_status"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default="BDT"
    )
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Refund(UUIDPrimaryKeyMixin, Base):
    """Refund request/record, per ERD §5.13. Phase 5 only ever creates
    rows in `requested` status (BR-ORD-003: "refunds require business
    approval") — the approval-to-money-movement workflow is V2 scope
    per docs/Implementation Plan.md.
    """

    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested', 'approved', 'rejected', 'completed')",
            name="ck_refunds_status",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="requested", server_default="requested"
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
