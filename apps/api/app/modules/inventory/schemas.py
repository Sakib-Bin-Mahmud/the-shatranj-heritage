import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdjustInventoryRequest(BaseModel):
    change_type: str = Field(pattern="^(restock|damage|adjustment)$")
    quantity_delta: int
    note: str | None = None


class InventoryResponse(BaseModel):
    id: uuid.UUID
    product_variant_id: uuid.UUID
    variant_sku: str
    variant_name: str
    product_name: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_threshold: int
    is_low_stock: bool

    model_config = {"from_attributes": True}


class InventoryTransactionResponse(BaseModel):
    id: uuid.UUID
    product_variant_id: uuid.UUID
    change_type: str
    quantity_delta: int
    reference_type: str | None
    reference_id: uuid.UUID | None
    note: str | None
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class InventoryListResponse(BaseModel):
    items: list[InventoryResponse]
    meta: PaginationMeta


class InventoryTransactionListResponse(BaseModel):
    items: list[InventoryTransactionResponse]
    meta: PaginationMeta
