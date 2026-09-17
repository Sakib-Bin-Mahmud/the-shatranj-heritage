import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Storefront account, per ERD §5.1. `email` and `mobile_number` are
    both nullable since registration allows either (FR-AUTH-001/002);
    at least one is required, enforced by a CHECK constraint.
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL", name="ck_customers_identifier_present"
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')", name="ck_customers_status"
        ),
    )

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    preferred_language: Mapped[str] = mapped_column(
        String(5), nullable=False, default="en", server_default="en"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )

    addresses: Mapped[list["CustomerAddress"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class CustomerAddress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Delivery/billing address, per ERD §5.2. Multiple per customer
    (US-CUS-003); exactly one `is_default` is enforced at the service
    layer, not the database, per the ERD's own note.
    """

    __tablename__ = "customer_addresses"
    __table_args__ = (
        CheckConstraint(
            "address_type IN ('shipping', 'billing', 'both')", name="ck_customer_addresses_type"
        ),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(
        String(2), nullable=False, default="BD", server_default="BD"
    )
    address_type: Mapped[str] = mapped_column(String(10), nullable=False, default="shipping")
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    customer: Mapped[Customer] = relationship(back_populates="addresses")
