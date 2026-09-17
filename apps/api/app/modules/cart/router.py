import secrets
import uuid

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import get_optional_customer
from app.modules.cart import service as cart_service
from app.modules.cart.schemas import AddCartItemRequest, UpdateCartItemRequest
from app.modules.customers.models import Customer

router = APIRouter(prefix="/cart", tags=["Cart"])

CART_SESSION_COOKIE = "cart_session_id"
CART_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days


def _set_guest_cookie(response: Response, session_id: str) -> None:
    settings = get_settings()
    response.set_cookie(
        CART_SESSION_COOKIE,
        session_id,
        max_age=CART_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=not settings.debug,
    )


async def _resolve_cart(
    session: AsyncSession,
    response: Response,
    customer: Customer | None,
    cart_session_id: str | None,
):
    """Guest carts are identified by the `cart_session_id` cookie;
    authenticated requests resolve via `customer_id` instead (API
    Specification §4 `POST /cart/items`). A guest visiting for the
    first time gets a fresh cookie issued right away, before they've
    added anything, so the same cart is found on their next request.
    """
    if customer:
        return await cart_service.get_or_create_cart(session, customer_id=customer.id)

    session_id = cart_session_id or secrets.token_urlsafe(32)
    if session_id != cart_session_id:
        _set_guest_cookie(response, session_id)
    return await cart_service.get_or_create_cart(session, session_id=session_id)


@router.get("")
async def get_cart(
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CRT-004/006. Self-heals the cart against current stock/product
    status (US-CRT-009) before returning it, surfacing any adjustment
    as a warning rather than silently changing the customer's cart."""
    cart = await _resolve_cart(session, response, customer, cart_session_id)
    warnings = await cart_service.revalidate_cart(session, cart)
    await session.commit()

    data = await cart_service.build_cart_response(session, cart)
    data["warnings"] = warnings
    return success_envelope(data=data)


@router.post("/items", status_code=201)
async def add_cart_item(
    payload: AddCartItemRequest,
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CRT-001. Quantity is capped by available inventory at
    add-time (US-CRT-002/009)."""
    cart = await _resolve_cart(session, response, customer, cart_session_id)
    await cart_service.add_item(
        session, cart, product_variant_id=payload.product_variant_id, quantity=payload.quantity
    )
    await session.commit()

    cart = await cart_service.get_cart_by_id(session, cart.id)
    return success_envelope(data=await cart_service.build_cart_response(session, cart))


@router.patch("/items/{item_id}")
async def update_cart_item(
    item_id: uuid.UUID,
    payload: UpdateCartItemRequest,
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CRT-002."""
    cart = await _resolve_cart(session, response, customer, cart_session_id)
    await cart_service.update_item_quantity(session, cart, item_id, payload.quantity)
    await session.commit()

    cart = await cart_service.get_cart_by_id(session, cart.id)
    return success_envelope(data=await cart_service.build_cart_response(session, cart))


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: uuid.UUID,
    response: Response,
    customer: Customer | None = Depends(get_optional_customer),
    cart_session_id: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """US-CRT-003."""
    cart = await _resolve_cart(session, response, customer, cart_session_id)
    await cart_service.remove_item(session, cart, item_id)
    await session.commit()

    cart = await cart_service.get_cart_by_id(session, cart.id)
    return success_envelope(data=await cart_service.build_cart_response(session, cart))
