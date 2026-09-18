import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import AdminPrincipal, require_permission
from app.modules.orders import service as orders_service
from app.modules.shipping import service as shipping_service
from app.modules.shipping.schemas import UpdateShipmentStatusRequest

admin_router = APIRouter(prefix="/admin/shipments", tags=["Admin - Shipping"])


@admin_router.patch("/{shipment_id}/status")
async def admin_update_shipment_status(
    shipment_id: uuid.UUID,
    payload: UpdateShipmentStatusRequest,
    admin: AdminPrincipal = Depends(require_permission("orders.write")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-SHP-003/004. Delivery is the one status that also completes
    the order (BR-ORD-003, US-SHP-004's "order timeline reflects the
    delivery event") — orchestrated here rather than inside
    shipping/service.py, which stays independent of the order state
    machine (see that module's update_shipment_status docstring)."""
    shipment = await shipping_service.get_shipment_or_404(session, shipment_id)
    await shipping_service.update_shipment_status(session, shipment, payload.status, admin.id)

    if payload.status == "delivered":
        order = await orders_service.get_order_or_404(session, shipment.order_id)
        # BR-ORD-004 / US-SHP-004: delivery notification is Phase 7's
        # notification service — logged here as the retrofit point,
        # per docs/Implementation Plan.md Phase 7 scope.
        await orders_service.admin_update_order_status(session, order, "delivered", admin.id)

    await session.commit()
    return success_envelope(data=orders_service.build_shipment_response(shipment))
