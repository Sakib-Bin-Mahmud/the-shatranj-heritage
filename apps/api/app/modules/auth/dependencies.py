import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import AppError
from app.modules.auth.models import AdminUser
from app.modules.auth.security import decode_token
from app.modules.customers.models import Customer

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthenticated() -> AppError:
    return AppError(status_code=401, code="UNAUTHENTICATED", message="Authentication required.")


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Customer:
    if not credentials:
        raise _unauthenticated()

    claims = decode_token(credentials.credentials, "customer_access")
    customer = await session.get(Customer, uuid.UUID(claims["sub"]))
    if not customer or customer.status != "active":
        raise _unauthenticated()
    return customer


async def get_optional_customer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Customer | None:
    """For Public/Customer endpoints (cart) that behave differently for
    a guest vs. a logged-in customer but never require login. A token
    that IS supplied must still be valid — this only makes the token
    itself optional, not tolerant of a bad one.
    """
    if not credentials:
        return None
    return await get_current_customer(credentials, session)


@dataclass(frozen=True)
class AdminPrincipal:
    """The authenticated admin, plus the permission codes granted by
    their roles at token-issue time (embedded in the access token so
    RBAC checks don't need a roles/permissions join on every request).
    """

    id: uuid.UUID
    email: str
    permissions: frozenset[str]


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPrincipal:
    if not credentials:
        raise _unauthenticated()

    claims = decode_token(credentials.credentials, "admin_access")
    admin = await session.get(AdminUser, uuid.UUID(claims["sub"]))
    if not admin or admin.status != "active":
        raise _unauthenticated()

    return AdminPrincipal(
        id=admin.id, email=admin.email, permissions=frozenset(claims.get("permissions", []))
    )


def require_permission(code: str) -> Callable:
    async def checker(admin: AdminPrincipal = Depends(get_current_admin)) -> AdminPrincipal:
        if code not in admin.permissions:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
            )
        return admin

    return checker
