import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditLog, record_audit_log
from app.core.responses import AppError
from app.modules.admin.schemas import CreateStaffRequest, UpdateShippingRateRequest
from app.modules.auth.models import AdminUser, Role
from app.modules.auth.security import hash_password
from app.modules.shipping.models import ShippingRate


async def _get_roles_by_names(session: AsyncSession, role_names: list[str]) -> list[Role]:
    roles = list(await session.scalars(select(Role).where(Role.name.in_(role_names))))
    found_names = {role.name for role in roles}
    missing = set(role_names) - found_names
    if missing:
        raise AppError(
            status_code=400,
            code="UNKNOWN_ROLE",
            message=f"Unknown role(s): {', '.join(sorted(missing))}.",
        )
    return roles


async def list_roles(session: AsyncSession) -> list[Role]:
    """FR-ADM-007."""
    return list(
        await session.scalars(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        )
    )


async def create_staff_user(session: AsyncSession, data: CreateStaffRequest) -> AdminUser:
    """US-ADM-003. Mirrors scripts/create_admin_user.py's bootstrap logic,
    now exposed via the API for ongoing staff management."""
    existing = await session.scalar(select(AdminUser).where(AdminUser.email == data.email))
    if existing:
        raise AppError(
            status_code=409, code="EMAIL_ALREADY_EXISTS", message="Email is already in use."
        )

    roles = await _get_roles_by_names(session, data.role_names)

    staff = AdminUser(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    staff.roles.extend(roles)
    session.add(staff)
    await session.flush()
    return staff


async def admin_list_staff(
    session: AsyncSession, *, page: int, limit: int
) -> tuple[list[AdminUser], int]:
    total = await session.scalar(select(func.count()).select_from(AdminUser)) or 0
    items = await session.scalars(
        select(AdminUser)
        .options(selectinload(AdminUser.roles))
        .order_by(AdminUser.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(items), total


async def get_staff_or_404(session: AsyncSession, staff_id: uuid.UUID) -> AdminUser:
    staff = await session.scalar(
        select(AdminUser).where(AdminUser.id == staff_id).options(selectinload(AdminUser.roles))
    )
    if not staff:
        raise AppError(status_code=404, code="NOT_FOUND", message="Staff user not found.")
    return staff


async def assign_roles(
    session: AsyncSession, *, actor_id: uuid.UUID, staff_id: uuid.UUID, role_names: list[str]
) -> AdminUser:
    """US-ADM-004."""
    staff = await get_staff_or_404(session, staff_id)
    previous_roles = sorted(role.name for role in staff.roles)

    roles = await _get_roles_by_names(session, role_names)
    staff.roles = roles
    await session.flush()

    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=actor_id,
        action="staff.roles_updated",
        entity_type="admin_user",
        entity_id=staff.id,
        before={"roles": previous_roles},
        after={"roles": sorted(role_names)},
    )
    return staff


async def list_audit_logs(
    session: AsyncSession, *, page: int, limit: int, entity_type: str | None = None
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)

    total = await session.scalar(count_query) or 0
    items = await session.scalars(
        query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(items), total


async def list_shipping_rates(session: AsyncSession) -> list[ShippingRate]:
    return list(
        await session.scalars(select(ShippingRate).order_by(ShippingRate.zone, ShippingRate.method))
    )


async def get_shipping_rate_or_404(session: AsyncSession, rate_id: uuid.UUID) -> ShippingRate:
    rate = await session.get(ShippingRate, rate_id)
    if not rate:
        raise AppError(status_code=404, code="NOT_FOUND", message="Shipping rate not found.")
    return rate


async def update_shipping_rate(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    rate_id: uuid.UUID,
    data: UpdateShippingRateRequest,
) -> ShippingRate:
    """Fulfills Phase 6's deferred admin-configurability of shipping
    rates (BR-SHP-002)."""
    rate = await get_shipping_rate_or_404(session, rate_id)
    before = {
        "base_rate": str(rate.base_rate),
        "base_weight_grams": rate.base_weight_grams,
        "per_kg_rate": str(rate.per_kg_rate),
        "is_active": rate.is_active,
    }

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(rate, field, value)
    await session.flush()

    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=actor_id,
        action="shipping_rate.updated",
        entity_type="shipping_rate",
        entity_id=rate.id,
        before=before,
        after={
            "base_rate": str(rate.base_rate),
            "base_weight_grams": rate.base_weight_grams,
            "per_kg_rate": str(rate.per_kg_rate),
            "is_active": rate.is_active,
        },
    )
    return rate
