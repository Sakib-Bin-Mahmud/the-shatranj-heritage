import hashlib
import hmac
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PaymentInitiationResult:
    transaction_id: str
    redirect_url: str


class PaymentProvider(ABC):
    """Gateway integration point, per SRS Part 3 §17 ("integrations
    isolated behind service interfaces... providers replaceable with
    minimal code changes"). `payments/service.py` only ever talks to
    this interface, never to a concrete provider directly.
    """

    @abstractmethod
    async def initiate(
        self,
        *,
        order_number: str,
        amount: Decimal,
        currency: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        ipn_url: str,
    ) -> PaymentInitiationResult: ...

    @abstractmethod
    def verify_webhook_signature(self, raw_body: bytes, signature: str | None) -> bool: ...


class SSLCommerzProvider(PaymentProvider):
    """Real integration against SSLCommerz's session-init API. The
    webhook signature scheme here is HMAC-SHA256 over the raw request
    body using a shared secret — documented in
    docs/API Specification.md §6 as "illustrative, not final" pending
    SSLCommerz's actual current IPN contract at real integration time.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def initiate(
        self,
        *,
        order_number: str,
        amount: Decimal,
        currency: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        ipn_url: str,
    ) -> PaymentInitiationResult:
        transaction_id = f"SH-{uuid.uuid4().hex[:20]}"
        payload = {
            "store_id": self._settings.sslcommerz_store_id,
            "store_passwd": self._settings.sslcommerz_store_password,
            "total_amount": str(amount),
            "currency": currency,
            "tran_id": transaction_id,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "ipn_url": ipn_url,
            "cus_name": order_number,
            "product_category": "chess-equipment",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self._settings.sslcommerz_api_base_url}/gwprocess/v4/api.php", data=payload
            )
            response.raise_for_status()
            body = response.json()

        redirect_url = body.get("GatewayPageURL")
        if not redirect_url:
            logger.error("sslcommerz_initiate_failed", response=body)
            raise RuntimeError("SSLCommerz did not return a gateway URL.")

        return PaymentInitiationResult(transaction_id=transaction_id, redirect_url=redirect_url)

    def verify_webhook_signature(self, raw_body: bytes, signature: str | None) -> bool:
        if not signature:
            return False
        expected = hmac.new(
            self._settings.payment_webhook_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


class FakePaymentProvider(PaymentProvider):
    """Used when `settings.payment_provider == "fake"` (tests only — see
    tests/conftest.py, which sets PAYMENT_PROVIDER before app import the
    same way it points S3_ENDPOINT_URL at moto). Never makes a network
    call; uses the same HMAC scheme as SSLCommerzProvider so webhook
    signature verification is exercised for real, not skipped.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def initiate(
        self,
        *,
        order_number: str,
        amount: Decimal,
        currency: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        ipn_url: str,
    ) -> PaymentInitiationResult:
        transaction_id = f"FAKE-{uuid.uuid4().hex[:20]}"
        return PaymentInitiationResult(
            transaction_id=transaction_id,
            redirect_url=f"https://fake-gateway.test/pay/{transaction_id}",
        )

    def verify_webhook_signature(self, raw_body: bytes, signature: str | None) -> bool:
        if not signature:
            return False
        expected = hmac.new(
            self._settings.payment_webhook_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


def get_payment_provider() -> PaymentProvider:
    settings = get_settings()
    if settings.payment_provider == "fake":
        return FakePaymentProvider()
    return SSLCommerzProvider()
