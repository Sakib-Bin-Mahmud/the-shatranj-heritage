from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import router as catalog_router
from app.modules.cms.router import router as cms_router
from app.modules.inventory.router import router as inventory_router
from app.modules.notifications.router import router as notifications_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.shipping.router import router as shipping_router

api_router = APIRouter()

for module_router in (
    auth_router,
    catalog_router,
    inventory_router,
    cart_router,
    orders_router,
    payments_router,
    shipping_router,
    cms_router,
    admin_router,
    notifications_router,
):
    api_router.include_router(module_router)
