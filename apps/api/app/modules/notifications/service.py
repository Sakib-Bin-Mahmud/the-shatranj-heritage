import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.metrics import notifications_failed_total
from app.modules.notifications.models import NotificationLog
from app.modules.notifications.providers import NotificationChannel, get_notification_channel

logger = get_logger(__name__)

# Phase 7's required trigger set (FR-NOT-001..004, plus registration
# from the Implementation Plan's own Phase 7 scope list). Each value is
# (subject_template, body_template); `context` supplies the fields.
TEMPLATES: dict[str, tuple[str, str]] = {
    "registration_welcome": (
        "Welcome to The Shatranj Heritage, {full_name}!",
        "Hi {full_name}, thanks for creating an account with The Shatranj Heritage.",
    ),
    "password_reset": (
        "Reset your password",
        "Use this token to reset your password: {reset_token}. It expires shortly.",
    ),
    "order_confirmation": (
        "Order {order_number} confirmed",
        "Thank you! Your order {order_number} for {total_amount} {currency} has been placed.",
    ),
    "payment_confirmation": (
        "Payment received for order {order_number}",
        "We've received your payment of {amount} {currency} for order {order_number}.",
    ),
    "shipment_dispatched": (
        "Your order {order_number} is on its way",
        "Order {order_number} has been dispatched via {courier_name}. "
        "Tracking number: {tracking_number}.",
    ),
    "delivery_confirmation": (
        "Order {order_number} delivered",
        "Your order {order_number} has been delivered. We hope you enjoy your purchase!",
    ),
}


def _redact(context: dict[str, Any]) -> dict[str, Any]:
    """`notifications_log.payload` is a queryable, admin-visible ledger
    (see admin/router.py's audit/notification viewer) — a bearer
    credential like a password-reset token must never land in it, so
    any context key that looks like one is masked before persisting.
    The real value is still used for the actual send, above this call.
    """
    sensitive_markers = ("token", "secret", "password")
    return {
        key: "[REDACTED]" if any(marker in key.lower() for marker in sensitive_markers) else value
        for key, value in context.items()
    }


async def _send(
    session: AsyncSession,
    *,
    customer_id: uuid.UUID | None,
    channel: str,
    template_code: str,
    recipient: str,
    context: dict[str, Any],
    provider: NotificationChannel,
) -> None:
    """Never raises — a broken notification channel must never block
    the business operation that triggered it (NFR-AVL-003, echoing the
    same principle /health's docstring states for non-critical
    services). Always writes a ledger row, sent or failed.
    """
    subject_template, body_template = TEMPLATES[template_code]
    try:
        body = body_template.format(**context)
        if channel == "email":
            sent = await provider.send_email(
                recipient=recipient, subject=subject_template.format(**context), body=body
            )
        else:
            sent = await provider.send_sms(recipient=recipient, body=body)
        status = "sent" if sent else "failed"
    except Exception:
        logger.exception(
            "notification_send_failed", template_code=template_code, recipient=recipient
        )
        status = "failed"

    if status == "failed":
        notifications_failed_total.labels(channel=channel, template_code=template_code).inc()

    session.add(
        NotificationLog(
            customer_id=customer_id,
            channel=channel,
            template_code=template_code,
            recipient=recipient,
            status=status,
            payload=_redact(context),
        )
    )
    await session.flush()


async def notify(
    session: AsyncSession,
    *,
    customer_id: uuid.UUID | None,
    email: str | None,
    mobile_number: str | None,
    template_code: str,
    context: dict[str, Any],
    provider: NotificationChannel | None = None,
) -> None:
    """US-NOT-001: email when an address is on file, SMS too when a
    mobile number is — never neither, and never both required."""
    provider = provider or get_notification_channel()
    if email:
        await _send(
            session,
            customer_id=customer_id,
            channel="email",
            template_code=template_code,
            recipient=email,
            context=context,
            provider=provider,
        )
    if mobile_number:
        await _send(
            session,
            customer_id=customer_id,
            channel="sms",
            template_code=template_code,
            recipient=mobile_number,
            context=context,
            provider=provider,
        )
