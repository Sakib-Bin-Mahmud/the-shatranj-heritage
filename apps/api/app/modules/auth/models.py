import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

# --- RBAC: admin_users, roles, permissions, per ERD §5.3 ---------------

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

admin_user_roles = Table(
    "admin_user_roles",
    Base.metadata,
    Column(
        "admin_user_id",
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Role(UUIDPrimaryKeyMixin, Base):
    """One of the six staff roles from ERD §5.3 — seeded by a data
    migration in Phase 1; permissions are attached to a role as each
    owning module ships enforcement for them.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles"
    )


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class AdminUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Back-office staff account, per ERD §5.3."""

    __tablename__ = "admin_users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')", name="ck_admin_users_status"
        ),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list[Role]] = relationship(secondary=admin_user_roles)


# --- Sessions & password reset -----------------------------------------
# Not part of the ERD's data dictionary (which predates implementation),
# but required to make session invalidation (US-AUTH-006/007) and
# password reset (US-AUTH-005/006) actually work with stateless JWTs.
# See docs/Implementation Plan.md Phase 1.


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """One row per issued refresh token, keyed by the token's own `jti`
    claim as this row's `id`. Enables revocation (logout, password
    reset) and rotation (each `/auth/refresh` call issues a new token
    and revokes this one) without a stateful session store.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        CheckConstraint(
            "(customer_id IS NOT NULL) != (admin_user_id IS NOT NULL)",
            name="ck_refresh_tokens_exactly_one_owner",
        ),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True
    )
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PasswordResetToken(UUIDPrimaryKeyMixin, Base):
    """One-time password reset token for a customer (US-AUTH-005/006).
    The raw token is emailed/SMS'd (Phase 7 notification service; logged
    for now — see auth/service.py); only its hash is stored.
    """

    __tablename__ = "password_reset_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),)

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
