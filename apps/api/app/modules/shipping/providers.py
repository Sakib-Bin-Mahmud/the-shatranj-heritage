import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CourierBookingResult:
    tracking_number: str
    estimated_delivery_date: date | None


class CourierProvider(ABC):
    """Courier integration point, per BR-SHP-004 ("the business should
    support multiple logistics providers") and the same
    interface-isolation principle Phase 5 applied to payments (SRS
    Part 3 §17). `shipping/service.py` only ever talks to this
    interface, never to a concrete provider directly.
    """

    @abstractmethod
    async def create_shipment(
        self, *, order_id: uuid.UUID, courier_name: str
    ) -> CourierBookingResult: ...


class PathaoCourierProvider(CourierProvider):
    """Real integration against Pathao Courier's Merchant (Hermes) API.
    Like SSLCommerzProvider, the exact request/response shape here is
    illustrative — Pathao's API evolves and real integration needs
    live credentials and their current docs, which this environment
    has neither of.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            f"{self._settings.pathao_api_base_url}/aladdin/api/v1/issue-token",
            json={
                "client_id": self._settings.pathao_client_id,
                "client_secret": self._settings.pathao_client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

    async def create_shipment(
        self, *, order_id: uuid.UUID, courier_name: str
    ) -> CourierBookingResult:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token = await self._access_token(client)
            response = await client.post(
                f"{self._settings.pathao_api_base_url}/aladdin/api/v1/orders",
                headers={"Authorization": f"Bearer {token}"},
                json={"merchant_order_id": str(order_id)},
            )
            response.raise_for_status()
            body = response.json()

        consignment_id = body.get("consignment_id")
        if not consignment_id:
            logger.error("pathao_create_shipment_failed", response=body)
            raise RuntimeError("Pathao did not return a consignment ID.")

        return CourierBookingResult(
            tracking_number=consignment_id,
            estimated_delivery_date=date.today() + timedelta(days=3),
        )


class FakeCourierProvider(CourierProvider):
    """Used when `settings.courier_provider == "fake"` (tests only —
    see tests/conftest.py). Never makes a network call."""

    async def create_shipment(
        self, *, order_id: uuid.UUID, courier_name: str
    ) -> CourierBookingResult:
        return CourierBookingResult(
            tracking_number=f"FAKE-TRACK-{uuid.uuid4().hex[:12]}",
            estimated_delivery_date=date.today() + timedelta(days=3),
        )


def get_courier_provider() -> CourierProvider:
    settings = get_settings()
    if settings.courier_provider == "fake":
        return FakeCourierProvider()
    return PathaoCourierProvider()
