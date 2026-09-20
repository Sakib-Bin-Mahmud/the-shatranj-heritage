import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.responses import AppError
from app.modules.customers.models import Customer, CustomerAddress
from app.modules.customers.schemas import (
    CreateAddressRequest,
    UpdateAddressRequest,
    UpdateCustomerProfileRequest,
)


async def get_customer_or_404(session: AsyncSession, customer_id: uuid.UUID) -> Customer:
    customer = await session.get(Customer, customer_id)
    if not customer:
        raise AppError(status_code=404, code="NOT_FOUND", message="Customer not found.")
    return customer


async def update_profile(
    session: AsyncSession, customer: Customer, data: UpdateCustomerProfileRequest
) -> Customer:
    if data.full_name is not None:
        customer.full_name = data.full_name
    if data.preferred_language is not None:
        customer.preferred_language = data.preferred_language
    await session.flush()
    return customer


async def list_addresses(session: AsyncSession, customer_id: uuid.UUID) -> list[CustomerAddress]:
    result = await session.scalars(
        select(CustomerAddress)
        .where(CustomerAddress.customer_id == customer_id)
        .order_by(CustomerAddress.created_at)
    )
    return list(result)


async def _unset_other_defaults(
    session: AsyncSession, customer_id: uuid.UUID, except_id: uuid.UUID | None
) -> None:
    addresses = await list_addresses(session, customer_id)
    for address in addresses:
        if address.id != except_id:
            address.is_default = False


async def create_address(
    session: AsyncSession, customer_id: uuid.UUID, data: CreateAddressRequest
) -> CustomerAddress:
    existing = await list_addresses(session, customer_id)
    make_default = data.is_default or not existing

    address = CustomerAddress(
        customer_id=customer_id, **data.model_dump(exclude={"is_default"}), is_default=make_default
    )
    session.add(address)
    await session.flush()

    if make_default:
        await _unset_other_defaults(session, customer_id, except_id=address.id)

    return address


async def _get_owned_address_or_404(
    session: AsyncSession, customer_id: uuid.UUID, address_id: uuid.UUID
) -> CustomerAddress:
    address = await session.get(CustomerAddress, address_id)
    if not address or address.customer_id != customer_id:
        raise AppError(status_code=404, code="NOT_FOUND", message="Address not found.")
    return address


async def update_address(
    session: AsyncSession, customer_id: uuid.UUID, address_id: uuid.UUID, data: UpdateAddressRequest
) -> CustomerAddress:
    address = await _get_owned_address_or_404(session, customer_id, address_id)

    updates = data.model_dump(exclude_unset=True, exclude={"is_default"})
    for field, value in updates.items():
        setattr(address, field, value)

    if data.is_default is True:
        address.is_default = True
        await _unset_other_defaults(session, customer_id, except_id=address.id)
    elif data.is_default is False:
        address.is_default = False

    await session.flush()
    return address


async def delete_address(
    session: AsyncSession, customer_id: uuid.UUID, address_id: uuid.UUID
) -> None:
    address = await _get_owned_address_or_404(session, customer_id, address_id)
    was_default = address.is_default
    await session.delete(address)
    await session.flush()

    if was_default:
        remaining = await list_addresses(session, customer_id)
        if remaining:
            remaining[0].is_default = True


async def admin_list_customers(
    session: AsyncSession, *, page: int, limit: int, search: str | None
) -> tuple[list[Customer], int]:
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)

    if search:
        pattern = f"%{search}%"
        condition = or_(
            Customer.email.ilike(pattern),
            Customer.mobile_number.ilike(pattern),
            Customer.full_name.ilike(pattern),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = await session.scalar(count_query) or 0
    items = await session.scalars(
        query.order_by(Customer.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(items), total


async def admin_update_customer_status(
    session: AsyncSession, *, admin_id: uuid.UUID, customer_id: uuid.UUID, new_status: str
) -> Customer:
    customer = await get_customer_or_404(session, customer_id)
    previous_status = customer.status
    customer.status = new_status
    await session.flush()

    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=admin_id,
        action="customer.status_updated",
        entity_type="customer",
        entity_id=customer.id,
        before={"status": previous_status},
        after={"status": new_status},
    )
    return customer
