import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.config import get_settings
from app.core.responses import AppError
from app.modules.cart import service as cart_service
from app.modules.cart.models import Cart
from app.modules.catalog.service import quantity_available
from app.modules.customers.models import Customer, CustomerAddress
from app.modules.inventory.models import Inventory, InventoryTransaction
from app.modules.orders.models import Order, OrderItem
from app.modules.payments.models import Payment, Refund
from app.modules.payments.providers import PaymentProvider

# --- Shipping (Phase 5: flat/config-driven rate; BR-SHP-002's real
# location/weight-based calculation lands in Phase 6) ------------------

SHIPPING_METHOD_LABELS = {
    "standard": ("Standard Delivery", "3-5 business days"),
    "express": ("Express Delivery", "1-2 business days"),
}


def _shipping_rate(method: str) -> Decimal:
    settings = get_settings()
    rates = {
        "standard": Decimal(settings.shipping_standard_rate),
        "express": Decimal(settings.shipping_express_rate),
    }
    return rates[method]


def shipping_options() -> list[dict[str, Any]]:
    return [
        {"method": method, "label": label, "rate": _shipping_rate(method), "estimated_days": days}
        for method, (label, days) in SHIPPING_METHOD_LABELS.items()
    ]


# --- Address resolution (US-CHK-002) ----------------------------------


async def _resolve_shipping_address(
    session: AsyncSession,
    *,
    customer: Customer | None,
    address_id: uuid.UUID | None,
    inline_address: dict[str, Any] | None,
) -> dict[str, Any]:
    if address_id:
        if not customer:
            raise AppError(
                status_code=422,
                code="ADDRESS_REQUIRES_ACCOUNT",
                message="Guests must provide a shipping address directly.",
            )
        address = await session.scalar(
            select(CustomerAddress).where(
                CustomerAddress.id == address_id, CustomerAddress.customer_id == customer.id
            )
        )
        if not address:
            raise AppError(status_code=404, code="ADDRESS_NOT_FOUND", message="Address not found.")
        return {
            "label": address.label,
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "district": address.district,
            "postal_code": address.postal_code,
            "country": address.country,
        }

    if inline_address:
        return inline_address

    raise AppError(
        status_code=422, code="ADDRESS_REQUIRED", message="A shipping address is required."
    )


# --- Checkout quote (US-CHK-003/004) ------------------------------------


async def checkout_quote(
    session: AsyncSession, *, cart: Cart, shipping_method: str
) -> dict[str, Any]:
    if not cart.items:
        raise AppError(status_code=422, code="EMPTY_CART", message="Your cart is empty.")

    cart_data = await cart_service.build_cart_response(session, cart)
    subtotal = cart_data["subtotal"]
    shipping_amount = _shipping_rate(shipping_method)
    tax_amount = Decimal("0.00")
    discount_amount = Decimal("0.00")
    total_amount = subtotal + shipping_amount + tax_amount - discount_amount

    return {
        "subtotal": subtotal,
        "shipping_amount": shipping_amount,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "shipping_options": shipping_options(),
    }


# --- Order placement (US-CHK-006, FR-ORD-001, NFR-REL-001/004) -----------


async def _generate_order_number(session: AsyncSession) -> str:
    seq_value = await session.scalar(select(func.nextval("order_number_seq")))
    return f"SH-{date.today():%Y%m%d}-{seq_value:05d}"


async def _latest_payment(session: AsyncSession, order_id: uuid.UUID) -> Payment | None:
    return await session.scalar(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
    )


async def _find_by_idempotency_key(
    session: AsyncSession, key: str
) -> tuple[Order, Payment | None, None] | None:
    existing = await session.scalar(select(Order).where(Order.idempotency_key == key))
    if not existing:
        return None
    # No redirect_url on replay: a gateway session URL is one-time, so
    # a duplicate request is pointed at /payments/initiate to get a
    # fresh one rather than being handed a stale/expired link.
    return existing, await _latest_payment(session, existing.id), None


async def _initiate_payment(
    session: AsyncSession,
    *,
    order: Order,
    method: str,
    provider: PaymentProvider,
    base_url: str,
) -> tuple[Payment, str | None]:
    """Shared by order placement and the `/payments/initiate` retry
    endpoint. Always transitions the order to `awaiting_payment` —
    for COD that's immediate (BR-PAY-002 exempts it from online
    verification); for online methods it's "waiting on the gateway."
    Returns the redirect URL alongside the row since a gateway session
    URL is one-time/short-lived and isn't itself persisted.
    """
    if method == "cod":
        payment = Payment(
            order_id=order.id,
            method="cod",
            provider=None,
            status="pending",
            amount=order.total_amount,
            currency=order.currency,
        )
        session.add(payment)
        order.status = "awaiting_payment"
        await session.flush()
        return payment, None

    result = await provider.initiate(
        order_number=order.order_number,
        amount=order.total_amount,
        currency=order.currency,
        success_url=f"{base_url}/checkout/success",
        fail_url=f"{base_url}/checkout/failed",
        cancel_url=f"{base_url}/checkout/cancelled",
        ipn_url=f"{base_url}/api/v1/payments/webhook/sslcommerz",
    )
    payment = Payment(
        order_id=order.id,
        method=method,
        provider="sslcommerz",
        transaction_id=result.transaction_id,
        status="pending",
        amount=order.total_amount,
        currency=order.currency,
    )
    session.add(payment)
    order.status = "awaiting_payment"
    await session.flush()
    return payment, result.redirect_url


async def place_order(
    session: AsyncSession,
    *,
    cart: Cart,
    customer: Customer | None,
    guest_email: str | None,
    guest_phone: str | None,
    address_id: uuid.UUID | None,
    inline_address: dict[str, Any] | None,
    shipping_method: str,
    payment_method: str,
    idempotency_key: str | None,
    provider: PaymentProvider,
    base_url: str,
) -> tuple[Order, Payment | None, str | None]:
    """US-CHK-006. A single atomic transaction (the caller commits once,
    after this returns) covering: inventory validation + reservation,
    order + order_items creation, and payment initiation — per
    NFR-REL-004. `idempotency_key` satisfies NFR-REL-001: a replayed
    request (sequential retry, or a genuine race caught by the column's
    UNIQUE constraint) returns the original order rather than creating
    a duplicate.
    """
    if idempotency_key:
        replay = await _find_by_idempotency_key(session, idempotency_key)
        if replay:
            return replay

    if not cart.items:
        raise AppError(status_code=422, code="EMPTY_CART", message="Your cart is empty.")

    if not customer and not (guest_email or guest_phone):
        raise AppError(
            status_code=422,
            code="GUEST_CONTACT_REQUIRED",
            message="A guest order requires an email address or phone number.",
        )

    shipping_address = await _resolve_shipping_address(
        session, customer=customer, address_id=address_id, inline_address=inline_address
    )

    cart_data = await cart_service.build_cart_response(session, cart)
    subtotal = cart_data["subtotal"]
    shipping_amount = _shipping_rate(shipping_method)
    tax_amount = Decimal("0.00")
    discount_amount = Decimal("0.00")
    total_amount = subtotal + shipping_amount + tax_amount - discount_amount

    # Lock every affected inventory row up front and validate before
    # reserving anything, so a shortfall on item 3 of 3 never leaves
    # items 1-2 partially reserved.
    locked_inventory: dict[uuid.UUID, Inventory] = {}
    for item in cart.items:
        inventory = await session.scalar(
            select(Inventory)
            .where(Inventory.product_variant_id == item.product_variant_id)
            .with_for_update()
        )
        available = quantity_available(inventory)
        if item.quantity > available:
            raise AppError(
                status_code=422,
                code="INSUFFICIENT_STOCK",
                message=f"Only {available} unit(s) available for one of the items in your cart.",
            )
        locked_inventory[item.product_variant_id] = inventory

    for item in cart.items:
        locked_inventory[item.product_variant_id].quantity_reserved += item.quantity

    try:
        order = Order(
            order_number=await _generate_order_number(session),
            customer_id=customer.id if customer else None,
            guest_email=None if customer else guest_email,
            guest_phone=None if customer else guest_phone,
            status="pending",
            subtotal_amount=subtotal,
            discount_amount=discount_amount,
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency="BDT",
            shipping_address_snapshot=shipping_address,
            idempotency_key=idempotency_key,
        )
        session.add(order)
        await session.flush()
    except IntegrityError:
        # Two concurrent requests both passed the check above with the
        # same key; the DB's UNIQUE constraint is the real arbiter.
        # Roll back this attempt (which also releases the reservation
        # made above) and return the request that won the race.
        await session.rollback()
        replay = (
            await _find_by_idempotency_key(session, idempotency_key) if idempotency_key else None
        )
        if replay:
            return replay
        raise

    for item_data in cart_data["items"]:
        session.add(
            OrderItem(
                order_id=order.id,
                product_variant_id=item_data["product_variant_id"],
                product_name_snapshot=item_data["product_name"] or "Unknown product",
                sku_snapshot=item_data["sku"] or "",
                unit_price=item_data["unit_price_snapshot"],
                quantity=item_data["quantity"],
                line_total=item_data["line_total"],
            )
        )

    cart.status = "converted"
    await session.flush()

    # US-CHK-006 / BR-ORD-004: confirmation notification is Phase 7's
    # notification service — logged here as the retrofit point, per
    # docs/Implementation Plan.md Phase 7 scope.
    payment, redirect_url = await _initiate_payment(
        session, order=order, method=payment_method, provider=provider, base_url=base_url
    )
    return order, payment, redirect_url


async def retry_payment(
    session: AsyncSession,
    *,
    order: Order,
    method: str,
    provider: PaymentProvider,
    base_url: str,
) -> tuple[Payment, str | None]:
    """US-PAY-003: a customer whose payment attempt failed (or who
    abandoned the gateway page) can start a fresh attempt for the same
    order without it being re-created."""
    if order.status != "awaiting_payment":
        raise AppError(
            status_code=422,
            code="INVALID_ORDER_STATE",
            message="This order cannot accept a new payment attempt.",
        )
    already_paid = await session.scalar(
        select(Payment).where(Payment.order_id == order.id, Payment.status == "successful")
    )
    if already_paid:
        raise AppError(
            status_code=422, code="ALREADY_PAID", message="This order has already been paid."
        )

    return await _initiate_payment(
        session, order=order, method=method, provider=provider, base_url=base_url
    )


# --- Lifecycle (BR-ORD-003) --------------------------------------------

CANCELLABLE_STATUSES = {"pending", "awaiting_payment", "confirmed", "packed"}
INVENTORY_COMMITTED_STATUSES = {"confirmed", "packed"}

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"awaiting_payment", "confirmed", "cancelled"},
    "awaiting_payment": {"confirmed", "cancelled"},
    "confirmed": {"packed", "cancelled"},
    "packed": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
    "returned": set(),
    "refunded": set(),
}


async def confirm_order(session: AsyncSession, order: Order) -> Order:
    """Converts each item's reservation into a real deduction (reserved
    → sold, per docs/API Specification.md's webhook spec) and writes the
    audit ledger entry. Called by the payment webhook on success and by
    the admin status endpoint when manually confirming a COD order.
    """
    items = await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id))
    for item in items:
        inventory = await session.scalar(
            select(Inventory)
            .where(Inventory.product_variant_id == item.product_variant_id)
            .with_for_update()
        )
        if inventory:
            inventory.quantity_on_hand -= item.quantity
            inventory.quantity_reserved -= item.quantity
            session.add(
                InventoryTransaction(
                    product_variant_id=item.product_variant_id,
                    change_type="sale",
                    quantity_delta=-item.quantity,
                    reference_type="order",
                    reference_id=order.id,
                    note=f"Order {order.order_number} confirmed.",
                )
            )
    order.status = "confirmed"
    await session.flush()
    return order


async def cancel_order(session: AsyncSession, order: Order) -> Order:
    """US-ORD-003. Releases a still-just-reserved item back to
    available stock, or restores on-hand stock for an item whose
    reservation was already committed (see `confirm_order`) — and
    auto-files a refund request if a successful payment exists, so
    ops has something to act on (US-ORD-003's "payment refund workflow
    is triggered if necessary").
    """
    if order.status not in CANCELLABLE_STATUSES:
        raise AppError(
            status_code=422,
            code="ORDER_NOT_CANCELLABLE",
            message="This order can no longer be cancelled.",
        )

    already_committed = order.status in INVENTORY_COMMITTED_STATUSES
    items = await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id))
    for item in items:
        inventory = await session.scalar(
            select(Inventory)
            .where(Inventory.product_variant_id == item.product_variant_id)
            .with_for_update()
        )
        if not inventory:
            continue
        if already_committed:
            inventory.quantity_on_hand += item.quantity
            session.add(
                InventoryTransaction(
                    product_variant_id=item.product_variant_id,
                    change_type="return",
                    quantity_delta=item.quantity,
                    reference_type="order",
                    reference_id=order.id,
                    note=f"Order {order.order_number} cancelled.",
                )
            )
        else:
            inventory.quantity_reserved = max(0, inventory.quantity_reserved - item.quantity)

    order.status = "cancelled"

    successful_payment = await session.scalar(
        select(Payment).where(Payment.order_id == order.id, Payment.status == "successful")
    )
    if successful_payment:
        session.add(
            Refund(
                order_id=order.id,
                payment_id=successful_payment.id,
                amount=successful_payment.amount,
                reason="Order cancelled by customer.",
                status="requested",
            )
        )

    await session.flush()
    return order


async def admin_update_order_status(
    session: AsyncSession, order: Order, new_status: str, admin_id: uuid.UUID
) -> Order:
    """BR-ORD-003: forward-only transitions, enforced server-side.
    `cancelled` and `confirmed` reuse the same inventory-affecting
    logic as the customer-cancel/payment-webhook paths so there is one
    source of truth for what "cancelling" or "confirming" an order
    actually does to stock.
    """
    if new_status not in VALID_TRANSITIONS.get(order.status, set()):
        raise AppError(
            status_code=422,
            code="INVALID_TRANSITION",
            message=f"Cannot move an order from '{order.status}' to '{new_status}'.",
        )

    old_status = order.status
    if new_status == "cancelled":
        await cancel_order(session, order)
    elif new_status == "confirmed":
        await confirm_order(session, order)
    else:
        order.status = new_status
        await session.flush()

    await record_audit_log(
        session,
        actor_type="admin",
        actor_id=admin_id,
        action="order.status_updated",
        entity_type="order",
        entity_id=order.id,
        before={"status": old_status},
        after={"status": order.status},
    )
    await session.flush()
    return order


# --- Reads ---------------------------------------------------------------


async def get_order_or_404(session: AsyncSession, order_id: uuid.UUID) -> Order:
    order = await session.get(Order, order_id)
    if not order:
        raise AppError(status_code=404, code="NOT_FOUND", message="Order not found.")
    return order


async def get_customer_order_or_404(
    session: AsyncSession, customer_id: uuid.UUID, order_number: str
) -> Order:
    order = await session.scalar(
        select(Order).where(Order.order_number == order_number, Order.customer_id == customer_id)
    )
    if not order:
        raise AppError(status_code=404, code="NOT_FOUND", message="Order not found.")
    return order


async def get_customer_order_or_404_by_id(
    session: AsyncSession, customer_id: uuid.UUID, order_id: uuid.UUID
) -> Order:
    order = await session.scalar(
        select(Order).where(Order.id == order_id, Order.customer_id == customer_id)
    )
    if not order:
        raise AppError(status_code=404, code="NOT_FOUND", message="Order not found.")
    return order


async def list_customer_orders(
    session: AsyncSession, customer_id: uuid.UUID, *, page: int, limit: int
) -> tuple[list[Order], int]:
    query = select(Order).where(Order.customer_id == customer_id)
    count_query = select(func.count()).select_from(Order).where(Order.customer_id == customer_id)
    total = await session.scalar(count_query) or 0
    orders = await session.scalars(
        query.order_by(Order.placed_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(orders), total


async def admin_list_orders(
    session: AsyncSession, *, page: int, limit: int, status: str | None = None
) -> tuple[list[Order], int]:
    query = select(Order)
    count_query = select(func.count()).select_from(Order)
    if status:
        query = query.where(Order.status == status)
        count_query = count_query.where(Order.status == status)

    total = await session.scalar(count_query) or 0
    orders = await session.scalars(
        query.order_by(Order.placed_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(orders), total


async def build_order_summary(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "placed_at": order.placed_at,
    }


async def build_order_detail(session: AsyncSession, order: Order) -> dict[str, Any]:
    items = await session.scalars(
        select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.created_at)
    )
    payments = await session.scalars(
        select(Payment).where(Payment.order_id == order.id).order_by(Payment.created_at)
    )
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "customer_id": order.customer_id,
        "guest_email": order.guest_email,
        "guest_phone": order.guest_phone,
        "subtotal_amount": order.subtotal_amount,
        "discount_amount": order.discount_amount,
        "shipping_amount": order.shipping_amount,
        "tax_amount": order.tax_amount,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "shipping_address": order.shipping_address_snapshot,
        "billing_address": order.billing_address_snapshot,
        "placed_at": order.placed_at,
        "items": [
            {
                "id": item.id,
                "product_variant_id": item.product_variant_id,
                "product_name": item.product_name_snapshot,
                "sku": item.sku_snapshot,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "line_total": item.line_total,
            }
            for item in items
        ],
        "payments": [
            {
                "id": p.id,
                "method": p.method,
                "status": p.status,
                "amount": p.amount,
                "transaction_id": p.transaction_id,
                "paid_at": p.paid_at,
            }
            for p in payments
        ],
    }


async def admin_create_refund(
    session: AsyncSession,
    *,
    order: Order,
    payment_id: uuid.UUID,
    amount: Decimal,
    reason: str | None,
) -> Refund:
    """API Specification §4 `POST /admin/orders/{id}/refund`: records
    the request only (BR-ORD-003 — refunds require business approval);
    the approve/reject-and-move-money workflow is V2 scope."""
    payment = await session.get(Payment, payment_id)
    if not payment or payment.order_id != order.id:
        raise AppError(
            status_code=404, code="NOT_FOUND", message="Payment not found for this order."
        )

    refund = Refund(order_id=order.id, payment_id=payment.id, amount=amount, reason=reason)
    session.add(refund)
    await session.flush()
    return refund
