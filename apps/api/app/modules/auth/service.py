import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit_log
from app.core.logging import get_logger
from app.core.responses import AppError
from app.modules.auth.models import AdminUser, PasswordResetToken, RefreshToken, Role
from app.modules.auth.schemas import normalize_identifier
from app.modules.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.customers.models import Customer
from app.modules.notifications import service as notifications_service

logger = get_logger(__name__)

PASSWORD_RESET_TOKEN_TTL_MINUTES = 30


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def register_customer(
    session: AsyncSession,
    *,
    email: str | None,
    mobile_number: str | None,
    password: str,
    full_name: str,
) -> Customer:
    if email:
        existing = await session.scalar(select(Customer).where(Customer.email == email))
        if existing:
            raise AppError(
                status_code=409, code="EMAIL_ALREADY_EXISTS", message="Email is already registered."
            )
    if mobile_number:
        existing = await session.scalar(
            select(Customer).where(Customer.mobile_number == mobile_number)
        )
        if existing:
            raise AppError(
                status_code=409,
                code="MOBILE_ALREADY_EXISTS",
                message="Mobile number is already registered.",
            )

    customer = Customer(
        email=email,
        mobile_number=mobile_number,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    session.add(customer)
    await session.flush()

    await notifications_service.notify(
        session,
        customer_id=customer.id,
        email=customer.email,
        mobile_number=customer.mobile_number,
        template_code="registration_welcome",
        context={"full_name": customer.full_name},
    )
    return customer


async def authenticate_customer(
    session: AsyncSession, *, identifier: str, password: str
) -> Customer:
    identifier = normalize_identifier(identifier)
    customer = await session.scalar(
        select(Customer).where(
            (Customer.email == identifier) | (Customer.mobile_number == identifier)
        )
    )
    # Generic error regardless of which check failed, to avoid account
    # enumeration (docs/API Specification.md, POST /auth/login).
    if not customer or not verify_password(password, customer.password_hash):
        raise AppError(status_code=401, code="INVALID_CREDENTIALS", message="Invalid credentials.")
    if customer.status != "active":
        raise AppError(status_code=401, code="INVALID_CREDENTIALS", message="Invalid credentials.")
    return customer


async def authenticate_admin(session: AsyncSession, *, email: str, password: str) -> AdminUser:
    admin = await session.scalar(
        select(AdminUser)
        .options(selectinload(AdminUser.roles).selectinload(Role.permissions))
        .where(AdminUser.email == email)
    )
    if not admin or not verify_password(password, admin.password_hash):
        raise AppError(status_code=401, code="INVALID_CREDENTIALS", message="Invalid credentials.")
    if admin.status != "active":
        raise AppError(status_code=401, code="INVALID_CREDENTIALS", message="Invalid credentials.")

    admin.last_login_at = datetime.now(UTC)
    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=admin.id,
        action="admin.login",
        entity_type="admin_user",
        entity_id=admin.id,
    )
    return admin


async def _issue_tokens(
    session: AsyncSession,
    *,
    subject: uuid.UUID,
    customer_id: uuid.UUID | None,
    admin_user_id: uuid.UUID | None,
    access_type: str,
    refresh_type: str,
    extra_access_claims: dict | None = None,
) -> tuple[str, str]:
    access_token = create_access_token(subject, access_type, extra_access_claims)  # type: ignore[arg-type]
    refresh_token, jti, expires_at = create_refresh_token(subject, refresh_type)  # type: ignore[arg-type]

    session.add(
        RefreshToken(
            id=jti,
            customer_id=customer_id,
            admin_user_id=admin_user_id,
            token_hash=_hash_token(refresh_token),
            expires_at=expires_at,
        )
    )
    return access_token, refresh_token


async def issue_customer_tokens(session: AsyncSession, customer: Customer) -> tuple[str, str]:
    return await _issue_tokens(
        session,
        subject=customer.id,
        customer_id=customer.id,
        admin_user_id=None,
        access_type="customer_access",
        refresh_type="customer_refresh",
    )


async def issue_admin_tokens(session: AsyncSession, admin: AdminUser) -> tuple[str, str]:
    return await _issue_tokens(
        session,
        subject=admin.id,
        customer_id=None,
        admin_user_id=admin.id,
        access_type="admin_access",
        refresh_type="admin_refresh",
        extra_access_claims={
            "permissions": sorted({p.code for role in admin.roles for p in role.permissions})
        },
    )


async def _get_valid_refresh_token_row(
    session: AsyncSession, *, jti: str, raw_token: str
) -> RefreshToken:
    row = await session.get(RefreshToken, uuid.UUID(jti))
    now = datetime.now(UTC)
    if (
        not row
        or row.revoked_at is not None
        or row.expires_at.replace(tzinfo=UTC) < now
        or row.token_hash != _hash_token(raw_token)
    ):
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Invalid or expired token.")
    return row


async def refresh_customer_session(
    session: AsyncSession, raw_refresh_token: str
) -> tuple[str, str]:
    claims = decode_token(raw_refresh_token, "customer_refresh")
    row = await _get_valid_refresh_token_row(
        session, jti=claims["jti"], raw_token=raw_refresh_token
    )
    row.revoked_at = datetime.now(UTC)

    customer = await session.get(Customer, row.customer_id)
    if not customer or customer.status != "active":
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Invalid or expired token.")

    return await issue_customer_tokens(session, customer)


async def refresh_admin_session(session: AsyncSession, raw_refresh_token: str) -> tuple[str, str]:
    claims = decode_token(raw_refresh_token, "admin_refresh")
    row = await _get_valid_refresh_token_row(
        session, jti=claims["jti"], raw_token=raw_refresh_token
    )
    row.revoked_at = datetime.now(UTC)

    admin = await session.scalar(
        select(AdminUser)
        .options(selectinload(AdminUser.roles).selectinload(Role.permissions))
        .where(AdminUser.id == row.admin_user_id)
    )
    if not admin or admin.status != "active":
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Invalid or expired token.")

    return await issue_admin_tokens(session, admin)


async def logout(session: AsyncSession, raw_refresh_token: str) -> None:
    """Revokes only the session identified by this refresh token
    (US-AUTH-007) — other devices/sessions stay active."""
    try:
        claims = decode_token(raw_refresh_token, ("customer_refresh", "admin_refresh"))
    except AppError:
        # Logging out with an already-invalid token is a no-op, not an error.
        return

    row = await session.get(RefreshToken, uuid.UUID(claims["jti"]))
    if row and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)


async def request_password_reset(session: AsyncSession, identifier: str) -> str | None:
    """Also returns the raw reset token so the router can still echo it
    in debug mode (there's no real inbox to check locally without a
    live email/SMS vendor behind LoggingNotificationChannel — see
    auth/router.py). Returns None if the identifier isn't registered,
    without revealing that fact to the router/customer.
    """
    identifier = normalize_identifier(identifier)
    customer = await session.scalar(
        select(Customer).where(
            (Customer.email == identifier) | (Customer.mobile_number == identifier)
        )
    )
    if not customer:
        return None

    raw_token = secrets.token_urlsafe(32)
    session.add(
        PasswordResetToken(
            customer_id=customer.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES),
        )
    )
    await notifications_service.notify(
        session,
        customer_id=customer.id,
        email=customer.email,
        mobile_number=customer.mobile_number,
        template_code="password_reset",
        context={"reset_token": raw_token},
    )
    return raw_token


async def reset_password(session: AsyncSession, *, raw_token: str, new_password: str) -> None:
    token_hash = _hash_token(raw_token)
    row = await session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(UTC)
    if not row or row.used_at is not None or row.expires_at.replace(tzinfo=UTC) < now:
        raise AppError(
            status_code=400, code="INVALID_RESET_TOKEN", message="Invalid or expired reset token."
        )

    customer = await session.get(Customer, row.customer_id)
    if not customer:
        raise AppError(
            status_code=400, code="INVALID_RESET_TOKEN", message="Invalid or expired reset token."
        )

    customer.password_hash = hash_password(new_password)
    row.used_at = now

    # US-AUTH-006: existing sessions are invalidated after a successful reset.
    active_sessions = await session.scalars(
        select(RefreshToken).where(
            RefreshToken.customer_id == customer.id, RefreshToken.revoked_at.is_(None)
        )
    )
    for session_row in active_sessions:
        session_row.revoked_at = now
