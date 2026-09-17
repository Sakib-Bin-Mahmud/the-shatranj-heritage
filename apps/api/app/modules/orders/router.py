from fastapi import APIRouter, Depends, Query

from app.core.responses import success_envelope
from app.modules.auth.dependencies import get_current_customer
from app.modules.customers.models import Customer

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/")
async def list_my_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    customer: Customer = Depends(get_current_customer),
) -> dict:
    """US-CUS-004. Stub until Order Management ships in Phase 5 — always
    empty, but with the real response shape, so the customer-facing UI
    can be built against a stable contract ahead of that phase (see
    docs/Implementation Plan.md Phase 1)."""
    return success_envelope(
        data={"items": [], "meta": {"page": page, "limit": limit, "total": 0, "total_pages": 0}}
    )
