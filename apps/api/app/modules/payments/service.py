import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.metrics import payment_webhook_results_total
from app.core.responses import AppError
from app.modules.orders import service as orders_service
from app.modules.orders.models import Order
from app.modules.payments.models import Payment
from app.modules.payments.providers import PaymentProvider

logger = get_logger(__name__)


async def get_payment_or_404(session: AsyncSession, payment_id: uuid.UUID) -> Payment:
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise AppError(status_code=404, code="NOT_FOUND", message="Payment not found.")
    return payment


async def process_webhook(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    raw_body: bytes,
    signature: str | None,
    payload: dict[str, Any],
) -> None:
    """US-PAY-003/004. Per docs/API Specification.md's webhook spec: an
    authentic-but-otherwise-unprocessable notification (unknown
    transaction, already-processed payment) is swallowed rather than
    erroring, so the gateway isn't driven into an endless retry loop
    over something a retry can't fix — but a *forged* signature is
    rejected outright (that's a security event, not a processing
    hiccup), which is why signature verification happens first and
    raises instead of returning quietly.
    """
    if not provider.verify_webhook_signature(raw_body, signature):
        payment_webhook_results_total.labels(result="signature_invalid").inc()
        raise AppError(
            status_code=401,
            code="INVALID_SIGNATURE",
            message="Webhook signature verification failed.",
        )

    transaction_id = payload.get("transaction_id")
    payment = (
        await session.scalar(select(Payment).where(Payment.transaction_id == transaction_id))
        if transaction_id
        else None
    )
    if not payment:
        logger.warning("payment_webhook_unknown_transaction", transaction_id=transaction_id)
        payment_webhook_results_total.labels(result="unknown_transaction").inc()
        return

    if payment.status in ("successful", "failed"):
        # Idempotent replay (NFR-REL-003): already processed, nothing to do.
        payment_webhook_results_total.labels(result="already_processed").inc()
        return

    order = await session.get(Order, payment.order_id)
    if not order:
        logger.error("payment_webhook_order_missing", order_id=str(payment.order_id))
        payment_webhook_results_total.labels(result="order_missing").inc()
        return

    if payload.get("status") == "success":
        payment.status = "successful"
        payment.paid_at = datetime.now(UTC)
        payment.raw_response = payload
        await orders_service.confirm_order(session, order)
        await orders_service.send_payment_confirmation(session, order, payment)
        payment_webhook_results_total.labels(result="success").inc()
    else:
        payment.status = "failed"
        payment.raw_response = payload
        payment_webhook_results_total.labels(result="failed").inc()

    await session.flush()
