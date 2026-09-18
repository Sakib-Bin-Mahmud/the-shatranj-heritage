import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.modules.customers.schemas import AddressBase


class _AddressChoiceMixin(BaseModel):
    """US-CHK-002: either an existing address book entry or a one-off
    inline address (the only option for a guest, who has no address
    book) — never both, never neither."""

    address_id: uuid.UUID | None = None
    address: AddressBase | None = None

    @model_validator(mode="after")
    def _exactly_one_address(self) -> "_AddressChoiceMixin":
        if bool(self.address_id) == bool(self.address):
            raise ValueError("Provide exactly one of address_id or address.")
        return self


class CheckoutQuoteRequest(_AddressChoiceMixin):
    shipping_method: str = Field(pattern="^(standard|express)$")


class ShippingOption(BaseModel):
    method: str
    label: str
    rate: Decimal
    estimated_days: str


class CheckoutQuoteResponse(BaseModel):
    subtotal: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    shipping_options: list[ShippingOption]


class PlaceOrderRequest(_AddressChoiceMixin):
    shipping_method: str = Field(pattern="^(standard|express)$")
    payment_method: str = Field(pattern="^(bkash|nagad|rocket|card|cod)$")
    guest_email: str | None = None
    guest_phone: str | None = None


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_variant_id: uuid.UUID
    product_name: str
    sku: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class PaymentSummary(BaseModel):
    id: uuid.UUID
    method: str
    status: str
    amount: Decimal
    transaction_id: str | None
    paid_at: datetime | None


class OrderSummary(BaseModel):
    """Shape for GET /orders (list), per US-CUS-004/US-ORD-002."""

    id: uuid.UUID
    order_number: str
    status: str
    total_amount: Decimal
    currency: str
    placed_at: datetime


class OrderDetail(BaseModel):
    """US-ORD-004."""

    id: uuid.UUID
    order_number: str
    status: str
    customer_id: uuid.UUID | None
    guest_email: str | None
    guest_phone: str | None
    subtotal_amount: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    shipping_address: dict[str, Any]
    billing_address: dict[str, Any] | None
    placed_at: datetime
    items: list[OrderItemResponse]
    payments: list[PaymentSummary]


class AdminUpdateOrderStatusRequest(BaseModel):
    status: str = Field(pattern="^(confirmed|packed|shipped|delivered|cancelled)$")


class AdminCreateRefundRequest(BaseModel):
    payment_id: uuid.UUID
    amount: Decimal
    reason: str | None = None
