import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SalesReportResponse(BaseModel):
    from_date: date
    to_date: date
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_status: dict[str, int]


class RevenuePoint(BaseModel):
    period: date
    revenue: Decimal
    order_count: int


class RevenueReportResponse(BaseModel):
    from_date: date
    to_date: date
    group_by: str
    points: list[RevenuePoint]


class LowStockItem(BaseModel):
    product_variant_id: uuid.UUID
    sku: str
    variant_name: str
    product_name: str
    quantity_on_hand: int
    quantity_available: int
    reorder_threshold: int


class SlowMovingItem(BaseModel):
    product_variant_id: uuid.UUID
    sku: str
    variant_name: str
    product_name: str
    quantity_on_hand: int
    days_since_last_sale: int | None


class InventoryReportResponse(BaseModel):
    low_stock: list[LowStockItem]
    slow_moving: list[SlowMovingItem]


class CustomerGrowthPoint(BaseModel):
    period: date
    new_customers: int


class CustomerReportResponse(BaseModel):
    from_date: date
    to_date: date
    group_by: str
    total_customers: int
    new_customers: int
    repeat_customer_rate: float
    growth: list[CustomerGrowthPoint]


class TopSellingProduct(BaseModel):
    product_variant_id: uuid.UUID
    sku: str
    product_name: str
    quantity_sold: int
    revenue: Decimal


class TopSellingProductsResponse(BaseModel):
    from_date: date
    to_date: date
    items: list[TopSellingProduct]


class RefundStatusBreakdown(BaseModel):
    status: str
    count: int
    amount: Decimal


class RefundReportResponse(BaseModel):
    from_date: date
    to_date: date
    total_refunds: int
    total_refund_amount: Decimal
    by_status: list[RefundStatusBreakdown]
