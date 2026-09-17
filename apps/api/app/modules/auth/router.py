from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.rate_limit import rate_limit
from app.core.responses import success_envelope
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    AccessTokenResponse,
    AdminLoginRequest,
    AdminTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.modules.auth.security import decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])
admin_router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post(
    "/register",
    status_code=201,
    dependencies=[Depends(rate_limit("auth_register", limit=10, window_seconds=60))],
)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """US-AUTH-001 / US-AUTH-002, FR-AUTH-001."""
    customer = await auth_service.register_customer(
        session,
        email=payload.email,
        mobile_number=payload.mobile_number,
        password=payload.password,
        full_name=payload.full_name,
    )
    access_token, refresh_token = await auth_service.issue_customer_tokens(session, customer)
    await session.commit()

    return success_envelope(
        data=TokenResponse(
            customer=customer, access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Registration successful.",
    )


@router.post(
    "/login", dependencies=[Depends(rate_limit("auth_login", limit=10, window_seconds=60))]
)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    """US-AUTH-003, FR-AUTH-002."""
    customer = await auth_service.authenticate_customer(
        session, identifier=payload.identifier, password=payload.password
    )
    access_token, refresh_token = await auth_service.issue_customer_tokens(session, customer)
    await session.commit()

    return success_envelope(
        data=TokenResponse(
            customer=customer, access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Login successful.",
    )


@router.post("/refresh")
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    """FR-AUTH-002. Accepts either a customer or admin refresh token and
    rotates it, since the API contract exposes a single public endpoint
    for both (see docs/API Specification.md §3.1)."""
    claims = decode_token(payload.refresh_token, ("customer_refresh", "admin_refresh"))

    if claims["type"] == "customer_refresh":
        access_token, refresh_token = await auth_service.refresh_customer_session(
            session, payload.refresh_token
        )
    else:
        access_token, refresh_token = await auth_service.refresh_admin_session(
            session, payload.refresh_token
        )

    await session.commit()
    return success_envelope(
        data=AccessTokenResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump()
    )


@router.post("/logout")
async def logout(payload: LogoutRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    """US-AUTH-007. Takes the refresh token to revoke directly rather than
    an access-token header: the refresh token is what identifies the
    session, and logout shouldn't require a still-fresh access token."""
    await auth_service.logout(session, payload.refresh_token)
    await session.commit()
    return success_envelope(message="Logged out successfully.")


@router.post(
    "/forgot-password",
    dependencies=[Depends(rate_limit("auth_forgot_password", limit=5, window_seconds=60))],
)
async def forgot_password(
    payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """US-AUTH-005. Always returns success, whether or not the identifier
    is registered, to avoid account enumeration."""
    raw_token = await auth_service.request_password_reset(session, payload.identifier)
    await session.commit()

    data = None
    if get_settings().debug and raw_token:
        # Stopgap until Phase 7 wires a real email/SMS notification
        # service: surface the token so the flow is usable/testable
        # end to end. Never enabled when debug=False (see .env.example).
        data = {"debug_reset_token": raw_token}

    return success_envelope(
        data=data, message="If that account exists, password reset instructions have been sent."
    )


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """US-AUTH-006."""
    await auth_service.reset_password(
        session, raw_token=payload.token, new_password=payload.new_password
    )
    await session.commit()
    return success_envelope(message="Password has been reset successfully.")


@admin_router.post(
    "/login", dependencies=[Depends(rate_limit("admin_auth_login", limit=10, window_seconds=60))]
)
async def admin_login(
    payload: AdminLoginRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Staff login. Not itemized as its own path in docs/API
    Specification.md (which only lists admin *management* endpoints
    under §3.11), but required for any `/admin/...` RBAC-gated endpoint
    to be reachable at all — see docs/Implementation Plan.md Phase 1."""
    admin = await auth_service.authenticate_admin(
        session, email=payload.email, password=payload.password
    )
    access_token, refresh_token = await auth_service.issue_admin_tokens(session, admin)
    await session.commit()

    return success_envelope(
        data=AdminTokenResponse(
            admin={
                "id": admin.id,
                "email": admin.email,
                "full_name": admin.full_name,
                "roles": [role.name for role in admin.roles],
            },
            access_token=access_token,
            refresh_token=refresh_token,
        ).model_dump(),
        message="Login successful.",
    )


@admin_router.post("/logout")
async def admin_logout(
    payload: LogoutRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    await auth_service.logout(session, payload.refresh_token)
    await session.commit()
    return success_envelope(message="Logged out successfully.")
