import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class AssignCourierRequest(BaseModel):
    """US-SHP-002. `tracking_number` is optional — see
    shipping/service.py:assign_courier for what happens when it's
    left out."""

    courier_name: str = Field(min_length=1, max_length=100)
    tracking_number: str | None = Field(default=None, max_length=100)
    estimated_delivery_date: date | None = None


class UpdateShipmentStatusRequest(BaseModel):
    status: str = Field(pattern="^(dispatched|in_transit|delivered|failed)$")


class ShipmentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    courier_name: str | None
    tracking_number: str | None
    status: str
    estimated_delivery_date: date | None
    shipped_at: datetime | None
    delivered_at: datetime | None
