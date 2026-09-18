from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import require_permission
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import (
    CustomerReportResponse,
    InventoryReportResponse,
    RefundReportResponse,
    RevenueReportResponse,
    SalesReportResponse,
    TopSellingProductsResponse,
)

router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin - Reports"],
    dependencies=[Depends(require_permission("reports.read"))],
)


@router.get("/sales")
async def sales_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-RPT-001."""
    resolved_from, resolved_to = reports_service.resolve_date_range(from_date, to_date)
    data = await reports_service.get_sales_report(
        session, from_date=resolved_from, to_date=resolved_to
    )
    return success_envelope(data=SalesReportResponse.model_validate(data).model_dump())


@router.get("/revenue")
async def revenue_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    group_by: str = Query(default="day"),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-RPT-002."""
    resolved_from, resolved_to = reports_service.resolve_date_range(from_date, to_date)
    data = await reports_service.get_revenue_report(
        session, from_date=resolved_from, to_date=resolved_to, group_by=group_by
    )
    return success_envelope(data=RevenueReportResponse.model_validate(data).model_dump())


@router.get("/inventory")
async def inventory_report(
    slow_moving_days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-RPT-002."""
    data = await reports_service.get_inventory_report(session, slow_moving_days=slow_moving_days)
    return success_envelope(data=InventoryReportResponse.model_validate(data).model_dump())


@router.get("/customers")
async def customers_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    group_by: str = Query(default="day"),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-RPT-003."""
    resolved_from, resolved_to = reports_service.resolve_date_range(from_date, to_date)
    data = await reports_service.get_customer_report(
        session, from_date=resolved_from, to_date=resolved_to, group_by=group_by
    )
    return success_envelope(data=CustomerReportResponse.model_validate(data).model_dump())


@router.get("/products/top-selling")
async def top_selling_products(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-RPT-005."""
    resolved_from, resolved_to = reports_service.resolve_date_range(from_date, to_date)
    items = await reports_service.get_top_selling_products(
        session, from_date=resolved_from, to_date=resolved_to, limit=limit
    )
    response = TopSellingProductsResponse(from_date=resolved_from, to_date=resolved_to, items=items)
    return success_envelope(data=response.model_dump())


@router.get("/refunds")
async def refunds_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """FR-RPT-006."""
    resolved_from, resolved_to = reports_service.resolve_date_range(from_date, to_date)
    data = await reports_service.get_refund_report(
        session, from_date=resolved_from, to_date=resolved_to
    )
    return success_envelope(data=RefundReportResponse.model_validate(data).model_dump())
