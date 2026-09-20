import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import AdminPrincipal, require_permission
from app.modules.inventory import service as inventory_service
from app.modules.inventory.schemas import AdjustInventoryRequest, InventoryTransactionResponse

router = APIRouter(prefix="/admin/inventory", tags=["Admin - Inventory"])


def _pagination_meta(page: int, limit: int, total: int) -> dict:
    total_pages = (total + limit - 1) // limit if total else 0
    return {"page": page, "limit": limit, "total": total, "total_pages": total_pages}


@router.get("", dependencies=[Depends(require_permission("inventory.read"))])
async def list_inventory(
    low_stock: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-INV-002."""
    items, total = await inventory_service.list_inventory(
        session, page=page, limit=limit, low_stock_only=low_stock
    )
    return success_envelope(data={"items": items, "meta": _pagination_meta(page, limit, total)})


@router.patch("/{variant_id}/adjust")
async def adjust_inventory(
    variant_id: uuid.UUID,
    payload: AdjustInventoryRequest,
    admin: AdminPrincipal = Depends(require_permission("inventory.write")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-INV-001, BR-INV-003."""
    inventory = await inventory_service.adjust_inventory(
        session,
        product_variant_id=variant_id,
        admin_id=admin.id,
        change_type=payload.change_type,
        quantity_delta=payload.quantity_delta,
        note=payload.note,
    )
    await session.commit()
    return success_envelope(
        data={
            "id": inventory.id,
            "product_variant_id": inventory.product_variant_id,
            "quantity_on_hand": inventory.quantity_on_hand,
            "quantity_reserved": inventory.quantity_reserved,
            "quantity_available": inventory.quantity_on_hand - inventory.quantity_reserved,
        }
    )


@router.get(
    "/{variant_id}/transactions", dependencies=[Depends(require_permission("inventory.read"))]
)
async def list_transactions(
    variant_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-INV-003."""
    transactions, total = await inventory_service.list_transactions(
        session, variant_id, page=page, limit=limit
    )
    items = [InventoryTransactionResponse.model_validate(t).model_dump() for t in transactions]
    return success_envelope(data={"items": items, "meta": _pagination_meta(page, limit, total)})
