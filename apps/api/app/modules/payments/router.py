import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import AppError, success_envelope
from app.modules.auth.dependencies import get_current_customer
from app.modules.customers.models import Customer
from app.modules.orders import service as orders_service
from app.modules.payments import service as payments_service
from app.modules.payments.providers import PaymentProvider, get_payment_provider
from app.modules.payments.schemas import PaymentInitiateRequest

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate")
async def initiate_payment(
    payload: PaymentInitiateRequest,
    request: Request,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> dict:
    """US-PAY-001/002/003: (re)starts payment for an order that's still
    `awaiting_payment` — the retry path after a failed or abandoned
    attempt. Scoped to the order's own customer; guest orders retry
    implicitly through the confirmation page's own redirect instead."""
    order = await orders_service.get_customer_order_or_404_by_id(
        session, customer.id, payload.order_id
    )
    base_url = str(request.base_url).rstrip("/")

    payment, redirect_url = await orders_service.retry_payment(
        session, order=order, method=payload.method, provider=provider, base_url=base_url
    )
    await session.commit()

    return success_envelope(
        data={"payment_id": payment.id, "status": payment.status, "redirect_url": redirect_url}
    )


@router.post("/webhook/sslcommerz")
async def sslcommerz_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> dict:
    """US-PAY-003/004. Not customer-authenticated — authenticity is the
    signature check inside `process_webhook`. Always responds 200 once
    that check passes (per docs/API Specification.md §4), even if the
    payload turns out to reference nothing we can act on, so the
    gateway isn't driven into an endless retry loop."""
    raw_body = await request.body()
    payload = await request.json()

    await payments_service.process_webhook(
        session, provider=provider, raw_body=raw_body, signature=x_signature, payload=payload
    )
    await session.commit()
    return success_envelope(message="Webhook processed.")


@router.get("/{payment_id}/status")
async def get_payment_status(
    payment_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-PAY-004."""
    payment = await payments_service.get_payment_or_404(session, payment_id)
    order = await orders_service.get_order_or_404(session, payment.order_id)
    if order.customer_id != customer.id:
        raise AppError(status_code=404, code="NOT_FOUND", message="Payment not found.")

    return success_envelope(
        data={
            "id": payment.id,
            "order_id": payment.order_id,
            "method": payment.method,
            "status": payment.status,
            "amount": payment.amount,
            "transaction_id": payment.transaction_id,
            "paid_at": payment.paid_at,
        }
    )
