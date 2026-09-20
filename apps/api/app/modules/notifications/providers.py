from abc import ABC, abstractmethod

from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationChannel(ABC):
    """Delivery point for a single channel, per SRS Part 3 §17's
    interface-isolation principle (same pattern as PaymentProvider and
    CourierProvider). Unlike SSLCommerz/Pathao, no specific email/SMS
    vendor is named anywhere in the requirements — wiring in a real one
    (SendGrid, Twilio, etc.) is future work behind this same interface,
    not a Phase 7 gap.
    """

    @abstractmethod
    async def send_email(self, *, recipient: str, subject: str, body: str) -> bool: ...

    @abstractmethod
    async def send_sms(self, *, recipient: str, body: str) -> bool: ...


class LoggingNotificationChannel(NotificationChannel):
    """What actually ships for Phase 7: every send is logged and
    recorded in `notifications_log` (see notifications/service.py) so
    the full pipeline — trigger, render, "deliver", audit trail — is
    real and testable even without a live vendor behind it.
    """

    async def send_email(self, *, recipient: str, subject: str, body: str) -> bool:
        logger.info("notification_email_sent", recipient=recipient, subject=subject)
        return True

    async def send_sms(self, *, recipient: str, body: str) -> bool:
        logger.info("notification_sms_sent", recipient=recipient, body=body)
        return True


def get_notification_channel() -> NotificationChannel:
    return LoggingNotificationChannel()
