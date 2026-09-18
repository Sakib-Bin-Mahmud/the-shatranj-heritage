import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    """US-PAY-003: retries payment for an order already placed."""

    order_id: uuid.UUID
    method: str = Field(pattern="^(bkash|nagad|rocket|card|cod)$")


class PaymentInitiateResponse(BaseModel):
    payment_id: uuid.UUID
    status: str
    redirect_url: str | None = None


class PaymentStatusResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    method: str
    status: str
    amount: Decimal
    transaction_id: str | None
    paid_at: datetime | None
