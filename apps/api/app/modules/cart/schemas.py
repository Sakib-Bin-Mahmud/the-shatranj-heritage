import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    product_variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    """Shape returned inside `GET /cart`, per Product Backlog US-CRT-004
    (product image, name, variant, quantity, unit price, subtotal)."""

    id: uuid.UUID
    product_variant_id: uuid.UUID
    product_id: uuid.UUID | None
    product_name: str | None
    product_slug: str | None
    sku: str | None
    variant_name: str | None
    primary_image_url: str | None
    quantity: int
    unit_price_snapshot: Decimal
    line_total: Decimal
    max_available: int
    is_available: bool


class CartResponse(BaseModel):
    """Per US-CRT-004/005: cart contents plus the summary breakdown
    (subtotal, estimated shipping/tax, discount, grand total)."""

    id: uuid.UUID
    item_count: int
    items: list[CartItemResponse]
    subtotal: Decimal
    estimated_shipping: Decimal
    estimated_tax: Decimal
    discount_amount: Decimal
    total: Decimal
    warnings: list[str] = []
