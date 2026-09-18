import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.admin import service as admin_service
from app.modules.admin.schemas import (
    AssignRolesRequest,
    AuditLogEntry,
    CreateStaffRequest,
    ShippingRateResponse,
    UpdateShippingRateRequest,
)
from app.modules.auth.dependencies import AdminPrincipal, require_permission

router = APIRouter(prefix="/admin", tags=["Admin"])


def _staff_summary(staff) -> dict:
    return {
        "id": staff.id,
        "email": staff.email,
        "full_name": staff.full_name,
        "status": staff.status,
        "roles": [role.name for role in staff.roles],
    }


def _role_response(role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": sorted(p.code for p in role.permissions),
    }


@router.get("/roles", dependencies=[Depends(require_permission("staff.manage"))])
async def list_roles(session: AsyncSession = Depends(get_db_session)) -> dict:
    """FR-ADM-007."""
    roles = await admin_service.list_roles(session)
    return success_envelope(data=[_role_response(r) for r in roles])


@router.get("/users", dependencies=[Depends(require_permission("staff.manage"))])
async def list_staff(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ADM-003."""
    items, total = await admin_service.admin_list_staff(session, page=page, limit=limit)
    total_pages = (total + limit - 1) // limit if total else 0
    return success_envelope(
        data={
            "items": [_staff_summary(s) for s in items],
            "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
        }
    )


@router.post("/users", status_code=201)
async def create_staff(
    payload: CreateStaffRequest,
    admin: AdminPrincipal = Depends(require_permission("staff.manage")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ADM-003."""
    staff = await admin_service.create_staff_user(session, payload)
    await session.commit()
    return success_envelope(data=_staff_summary(staff))


@router.patch("/users/{staff_id}/roles")
async def assign_staff_roles(
    staff_id: uuid.UUID,
    payload: AssignRolesRequest,
    admin: AdminPrincipal = Depends(require_permission("staff.manage")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ADM-004."""
    staff = await admin_service.assign_roles(
        session, actor_id=admin.id, staff_id=staff_id, role_names=payload.role_names
    )
    await session.commit()
    return success_envelope(data=_staff_summary(staff))


@router.get("/audit-logs", dependencies=[Depends(require_permission("audit.read"))])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    entity_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """NFR-AUD-001: viewer for the admin/system action audit trail."""
    items, total = await admin_service.list_audit_logs(
        session, page=page, limit=limit, entity_type=entity_type
    )
    total_pages = (total + limit - 1) // limit if total else 0
    return success_envelope(
        data={
            "items": [AuditLogEntry.model_validate(a).model_dump() for a in items],
            "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
        }
    )


@router.get(
    "/settings/shipping-rates", dependencies=[Depends(require_permission("settings.manage"))]
)
async def list_shipping_rates(session: AsyncSession = Depends(get_db_session)) -> dict:
    """BR-SHP-002: admin-configurable shipping rates."""
    rates = await admin_service.list_shipping_rates(session)
    return success_envelope(
        data=[ShippingRateResponse.model_validate(r).model_dump() for r in rates]
    )


@router.patch("/settings/shipping-rates/{rate_id}")
async def update_shipping_rate(
    rate_id: uuid.UUID,
    payload: UpdateShippingRateRequest,
    admin: AdminPrincipal = Depends(require_permission("settings.manage")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """BR-SHP-002."""
    rate = await admin_service.update_shipping_rate(
        session, actor_id=admin.id, rate_id=rate_id, data=payload
    )
    await session.commit()
    return success_envelope(data=ShippingRateResponse.model_validate(rate).model_dump())
