import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import AdminPrincipal, get_current_customer, require_permission
from app.modules.customers import service as customers_service
from app.modules.customers.models import Customer
from app.modules.customers.schemas import (
    AddressResponse,
    AdminUpdateCustomerStatusRequest,
    CreateAddressRequest,
    CustomerProfile,
    UpdateAddressRequest,
    UpdateCustomerProfileRequest,
)

router = APIRouter(prefix="/customers", tags=["Customers"])
admin_router = APIRouter(prefix="/admin/customers", tags=["Admin - Customers"])


@router.get("/me")
async def get_my_profile(customer: Customer = Depends(get_current_customer)) -> dict:
    """US-CUS-001."""
    return success_envelope(data=CustomerProfile.model_validate(customer).model_dump())


@router.patch("/me")
async def update_my_profile(
    payload: UpdateCustomerProfileRequest,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-002."""
    customer = await customers_service.update_profile(session, customer, payload)
    await session.commit()
    return success_envelope(data=CustomerProfile.model_validate(customer).model_dump())


@router.get("/me/addresses")
async def list_my_addresses(
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-003."""
    addresses = await customers_service.list_addresses(session, customer.id)
    return success_envelope(
        data=[AddressResponse.model_validate(a).model_dump() for a in addresses]
    )


@router.post("/me/addresses", status_code=201)
async def add_my_address(
    payload: CreateAddressRequest,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-003."""
    address = await customers_service.create_address(session, customer.id, payload)
    await session.commit()
    return success_envelope(data=AddressResponse.model_validate(address).model_dump())


@router.patch("/me/addresses/{address_id}")
async def update_my_address(
    address_id: uuid.UUID,
    payload: UpdateAddressRequest,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-003."""
    address = await customers_service.update_address(session, customer.id, address_id, payload)
    await session.commit()
    return success_envelope(data=AddressResponse.model_validate(address).model_dump())


@router.delete("/me/addresses/{address_id}", status_code=200)
async def delete_my_address(
    address_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-003."""
    await customers_service.delete_address(session, customer.id, address_id)
    await session.commit()
    return success_envelope(message="Address removed.")


@admin_router.get("", dependencies=[Depends(require_permission("customers.read"))])
async def admin_list_customers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-ADM-004."""
    items, total = await customers_service.admin_list_customers(
        session, page=page, limit=limit, search=search
    )
    total_pages = (total + limit - 1) // limit if total else 0
    return success_envelope(
        data={
            "items": [CustomerProfile.model_validate(c).model_dump() for c in items],
            "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
        }
    )


@admin_router.get("/{customer_id}", dependencies=[Depends(require_permission("customers.read"))])
async def admin_get_customer(
    customer_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-ADM-004."""
    customer = await customers_service.get_customer_or_404(session, customer_id)
    return success_envelope(data=CustomerProfile.model_validate(customer).model_dump())


@admin_router.patch("/{customer_id}/status")
async def admin_update_customer_status(
    customer_id: uuid.UUID,
    payload: AdminUpdateCustomerStatusRequest,
    admin: AdminPrincipal = Depends(require_permission("customers.manage")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-ADM-004."""
    customer = await customers_service.admin_update_customer_status(
        session, admin_id=admin.id, customer_id=customer_id, new_status=payload.status
    )
    await session.commit()
    return success_envelope(data=CustomerProfile.model_validate(customer).model_dump())
