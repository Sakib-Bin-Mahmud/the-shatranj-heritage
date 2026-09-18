from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.auth.router import admin_router as auth_admin_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import admin_router as catalog_admin_router
from app.modules.catalog.router import router as catalog_router
from app.modules.cms.router import router as cms_router
from app.modules.customers.router import admin_router as customers_admin_router
from app.modules.customers.router import router as customers_router
from app.modules.inventory.router import router as inventory_router
from app.modules.notifications.router import router as notifications_router
from app.modules.orders.router import admin_router as orders_admin_router
from app.modules.orders.router import checkout_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.shipping.router import admin_router as shipping_admin_router

api_router = APIRouter()

for module_router in (
    auth_router,
    auth_admin_router,
    customers_router,
    customers_admin_router,
    catalog_router,
    catalog_admin_router,
    inventory_router,
    cart_router,
    checkout_router,
    orders_router,
    orders_admin_router,
    payments_router,
    shipping_admin_router,
    cms_router,
    admin_router,
    notifications_router,
):
    api_router.include_router(module_router)
