import uuid

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.rate_limit import rate_limit
from app.core.responses import success_envelope
from app.modules.auth.dependencies import (
    AdminPrincipal,
    get_current_customer,
    get_optional_customer,
    require_permission,
)
from app.modules.cart.router import resolve_cart
from app.modules.customers.models import Customer
from app.modules.orders import service as orders_service
from app.modules.orders.schemas import (
    AdminCreateRefundRequest,
    AdminUpdateOrderStatusRequest,
    CheckoutQuoteRequest,
    OrderDetail,
    PlaceOrderRequest,
)
from app.modules.payments.providers import PaymentProvider, get_payment_provider
from app.modules.shipping import service as shipping_service
from app.modules.shipping.providers import CourierProvider, get_courier_provider
from app.modules.shipping.schemas import AssignCourierRequest

checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])
router = APIRouter(prefix="/orders", tags=["Orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["Admin - Orders"])


def _pagination_meta(page: int, limit: int, total: int) -> dict:
    total_pages = (total + limit - 1) // limit if total else 0
    return {"page": page, "limit": limit, "total": total, "total_pages": total_pages}


def _order_detail_response(data: dict) -> dict:
    return OrderDetail(**data).model_dump()


# --- Checkout (US-CHK-001..004) -----------------------------------------


@checkout_router.post(
    "/quote",
    dependencies=[Depends(rate_limit("checkout_quote", limit=30, window_seconds=60))],
)
async def get_checkout_quote(
    payload: CheckoutQuoteRequest,
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CHK-003/004. Stateless preview — no record created, no
    inventory touched. Shipping cost is real (BR-SHP-002: location +
    weight), so a different address or method changes the total."""
    cart = await resolve_cart(session, response, customer, cart_session_id)
    quote = await orders_service.checkout_quote(
        session,
        cart=cart,
        customer=customer,
        address_id=payload.address_id,
        inline_address=payload.address.model_dump() if payload.address else None,
        shipping_method=payload.shipping_method,
    )
    return success_envelope(data=quote)


# --- Order placement (US-CHK-006) ---------------------------------------


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(rate_limit("place_order", limit=20, window_seconds=60))],
)
async def place_order(
    payload: PlaceOrderRequest,
    request: Request,
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db_session),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> dict:
    """US-CHK-006, FR-ORD-001, NFR-REL-001. `Idempotency-Key` is a
    client-generated token (e.g. a UUID) that must be stable across
    retries of the *same* checkout attempt and unique across distinct
    ones."""
    cart = await resolve_cart(session, response, customer, cart_session_id)
    base_url = str(request.base_url).rstrip("/")

    order, payment, redirect_url = await orders_service.place_order(
        session,
        cart=cart,
        customer=customer,
        guest_email=payload.guest_email,
        guest_phone=payload.guest_phone,
        address_id=payload.address_id,
        inline_address=payload.address.model_dump() if payload.address else None,
        shipping_method=payload.shipping_method,
        payment_method=payload.payment_method,
        idempotency_key=idempotency_key,
        provider=provider,
        base_url=base_url,
    )
    await session.commit()

    payment_data = None
    if payment and payment.method != "cod":
        payment_data = {"redirect_url": redirect_url}

    return success_envelope(
        data={
            "order": await orders_service.build_order_summary(order),
            "payment": payment_data,
        },
        message="Order placed successfully.",
    )


# --- Customer order history / detail / cancellation ------------------


@router.get("")
async def list_my_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CUS-004, US-ORD-002. Replaces the Phase 1 always-empty stub."""
    orders, total = await orders_service.list_customer_orders(
        session, customer.id, page=page, limit=limit
    )
    items = [await orders_service.build_order_summary(o) for o in orders]
    return success_envelope(data={"items": items, "meta": _pagination_meta(page, limit, total)})


@router.get("/{order_number}")
async def get_my_order(
    order_number: str,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ORD-004."""
    order = await orders_service.get_customer_order_or_404(session, customer.id, order_number)
    detail = await orders_service.build_order_detail(session, order)
    return success_envelope(data=_order_detail_response(detail))


@router.post("/{order_number}/cancel")
async def cancel_my_order(
    order_number: str,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ORD-003."""
    order = await orders_service.get_customer_order_or_404(session, customer.id, order_number)
    await orders_service.cancel_order(session, order)
    await session.commit()
    return success_envelope(data=await orders_service.build_order_summary(order))


@router.get("/{order_number}/shipment")
async def get_my_order_shipment(
    order_number: str,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-SHP-003: tracking number, status, and estimated delivery date
    once a courier has been assigned."""
    order = await orders_service.get_customer_order_or_404(session, customer.id, order_number)
    shipment = await shipping_service.get_shipment_by_order_or_404(session, order.id)
    return success_envelope(data=orders_service.build_shipment_response(shipment))


# --- Admin (Order Manager+) ---------------------------------------------


@admin_router.get("", dependencies=[Depends(require_permission("orders.read"))])
async def admin_list_orders(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-ADM-003."""
    orders, total = await orders_service.admin_list_orders(
        session, page=page, limit=limit, status=status
    )
    items = [await orders_service.build_order_summary(o) for o in orders]
    return success_envelope(data={"items": items, "meta": _pagination_meta(page, limit, total)})


@admin_router.get("/{order_id}", dependencies=[Depends(require_permission("orders.read"))])
async def admin_get_order(
    order_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-ADM-003."""
    order = await orders_service.get_order_or_404(session, order_id)
    detail = await orders_service.build_order_detail(session, order)
    return success_envelope(data=_order_detail_response(detail))


@admin_router.patch("/{order_id}/status")
async def admin_update_order_status(
    order_id: uuid.UUID,
    payload: AdminUpdateOrderStatusRequest,
    admin: AdminPrincipal = Depends(require_permission("orders.write")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-ORD-002/003, BR-ORD-003."""
    order = await orders_service.get_order_or_404(session, order_id)
    await orders_service.admin_update_order_status(session, order, payload.status, admin.id)
    await session.commit()
    detail = await orders_service.build_order_detail(session, order)
    return success_envelope(data=_order_detail_response(detail))


@admin_router.post(
    "/{order_id}/refund",
    status_code=201,
    dependencies=[Depends(require_permission("orders.write"))],
)
async def admin_request_refund(
    order_id: uuid.UUID,
    payload: AdminCreateRefundRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-PAY-005, BR-ORD-003 ("refunds require business approval") —
    records the request only; approval/money-movement is V2 scope."""
    order = await orders_service.get_order_or_404(session, order_id)
    refund = await orders_service.admin_create_refund(
        session,
        order=order,
        payment_id=payload.payment_id,
        amount=payload.amount,
        reason=payload.reason,
    )
    await session.commit()
    return success_envelope(
        data={
            "id": refund.id,
            "order_id": refund.order_id,
            "payment_id": refund.payment_id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason,
        }
    )


@admin_router.post("/{order_id}/shipment", status_code=201)
async def admin_assign_shipment(
    order_id: uuid.UUID,
    payload: AssignCourierRequest,
    admin: AdminPrincipal = Depends(require_permission("orders.write")),
    session: AsyncSession = Depends(get_db_session),
    provider: CourierProvider = Depends(get_courier_provider),
) -> dict:
    """US-SHP-002. Requires the order to be `packed`; on success the
    order moves to `shipped` (see orders/service.py:admin_assign_shipment)."""
    order = await orders_service.get_order_or_404(session, order_id)
    shipment = await orders_service.admin_assign_shipment(
        session,
        order=order,
        courier_name=payload.courier_name,
        tracking_number=payload.tracking_number,
        estimated_delivery_date=payload.estimated_delivery_date,
        provider=provider,
        admin_id=admin.id,
    )
    await session.commit()
    return success_envelope(data=orders_service.build_shipment_response(shipment))
