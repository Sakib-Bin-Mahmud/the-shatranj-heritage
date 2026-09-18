import uuid
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.responses import AppError
from app.modules.shipping.models import Shipment, ShippingRate
from app.modules.shipping.providers import CourierProvider

# --- Cost calculation (US-SHP-001, BR-SHP-002) --------------------------

SHIPPING_METHOD_LABELS = {
    "standard": ("Standard Delivery", "3-5 business days"),
    "express": ("Express Delivery", "1-2 business days"),
}


def resolve_zone(district: str) -> str:
    """BR-SHP-002's "Location" factor: the two-zone Dhaka / outside-Dhaka
    split is the standard shorthand Bangladeshi couriers price by —
    finer-grained zones are a V2+ refinement, not a Phase 6 gap."""
    return "dhaka" if district.strip().lower() == "dhaka" else "outside_dhaka"


async def _get_rate_or_404(session: AsyncSession, *, zone: str, method: str) -> ShippingRate:
    rate = await session.scalar(
        select(ShippingRate).where(
            ShippingRate.zone == zone,
            ShippingRate.method == method,
            ShippingRate.is_active.is_(True),
        )
    )
    if not rate:
        raise AppError(
            status_code=422,
            code="SHIPPING_UNAVAILABLE",
            message=f"No shipping rate is configured for {zone}/{method}.",
        )
    return rate


async def calculate_shipping(
    session: AsyncSession, *, district: str, method: str, total_weight_grams: int
) -> Decimal:
    """BR-SHP-002's "Location" + "Weight" factors. `base_rate` covers
    up to `base_weight_grams`; anything heavier is charged at
    `per_kg_rate` per additional kilogram (fractional kg rounded up
    to the next whole kg, matching how couriers actually bill)."""
    rate = await _get_rate_or_404(session, zone=resolve_zone(district), method=method)

    extra_grams = max(0, total_weight_grams - rate.base_weight_grams)
    extra_kg = (Decimal(extra_grams) / Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    extra_charge = extra_kg * rate.per_kg_rate
    return (rate.base_rate + extra_charge).quantize(Decimal("0.01"))


async def shipping_options(
    session: AsyncSession, *, district: str, total_weight_grams: int
) -> list[dict]:
    """US-CHK-003: every method's real cost for this address/weight,
    not just the one the customer has (or hasn't yet) selected."""
    options = []
    for method, (label, days) in SHIPPING_METHOD_LABELS.items():
        rate = await calculate_shipping(
            session, district=district, method=method, total_weight_grams=total_weight_grams
        )
        options.append({"method": method, "label": label, "rate": rate, "estimated_days": days})
    return options


# --- Shipment lifecycle (US-SHP-002/003/004) -----------------------------

SHIPMENT_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"dispatched", "failed"},
    "dispatched": {"in_transit", "failed"},
    "in_transit": {"delivered", "failed"},
    "delivered": set(),
    "failed": {"dispatched"},  # a redelivery attempt after a failed one
}


async def get_shipment_by_order_or_404(session: AsyncSession, order_id: uuid.UUID) -> Shipment:
    shipment = await session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if not shipment:
        raise AppError(status_code=404, code="NOT_FOUND", message="No shipment for this order yet.")
    return shipment


async def get_shipment_or_404(session: AsyncSession, shipment_id: uuid.UUID) -> Shipment:
    shipment = await session.get(Shipment, shipment_id)
    if not shipment:
        raise AppError(status_code=404, code="NOT_FOUND", message="Shipment not found.")
    return shipment


async def assign_courier(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    courier_name: str,
    tracking_number: str | None,
    estimated_delivery_date: date | None,
    provider: CourierProvider,
) -> Shipment:
    """US-SHP-002. `tracking_number` is optional: ops can type in a
    number obtained by phone/the courier's own dashboard, or leave it
    out and let the configured `CourierProvider` book the pickup and
    return one — either way a `Shipment` row always ends up with one.
    """
    existing = await session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if existing:
        raise AppError(
            status_code=422,
            code="SHIPMENT_ALREADY_EXISTS",
            message="This order already has a shipment.",
        )

    if not tracking_number:
        result = await provider.create_shipment(order_id=order_id, courier_name=courier_name)
        tracking_number = result.tracking_number
        estimated_delivery_date = estimated_delivery_date or result.estimated_delivery_date

    shipment = Shipment(
        order_id=order_id,
        courier_name=courier_name,
        tracking_number=tracking_number,
        status="pending",
        estimated_delivery_date=estimated_delivery_date,
    )
    session.add(shipment)
    await session.flush()
    return shipment


async def update_shipment_status(
    session: AsyncSession, shipment: Shipment, new_status: str, admin_id: uuid.UUID
) -> Shipment:
    """US-SHP-003/004, BR-ORD-003. Forward-only, mirroring the order
    state machine's own discipline. `dispatched`/`in_transit` don't
    touch the order (it's already `shipped`, set when the shipment was
    created); `delivered` is the one status that also completes the
    order — see shipping/router.py's admin shipment-status endpoint,
    which calls orders_service.admin_update_order_status() alongside
    this function rather than that logic living here (keeps this
    module independent of the order state machine)."""
    if new_status not in SHIPMENT_VALID_TRANSITIONS.get(shipment.status, set()):
        raise AppError(
            status_code=422,
            code="INVALID_TRANSITION",
            message=f"Cannot move a shipment from '{shipment.status}' to '{new_status}'.",
        )

    old_status = shipment.status
    shipment.status = new_status
    if new_status == "dispatched" and shipment.shipped_at is None:
        shipment.shipped_at = datetime.now(UTC)
    if new_status == "delivered":
        shipment.delivered_at = datetime.now(UTC)

    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=admin_id,
        action="shipment.status_updated",
        entity_type="shipment",
        entity_id=shipment.id,
        before={"status": old_status},
        after={"status": shipment.status},
    )
    await session.flush()
    return shipment
