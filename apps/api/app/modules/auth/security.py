import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.responses import AppError

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["customer_access", "customer_refresh", "admin_access", "admin_refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _encode(claims: dict[str, Any]) -> str:
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: uuid.UUID, token_type: TokenType, extra_claims: dict[str, Any] | None = None
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    claims.update(extra_claims or {})
    return _encode(claims)


def create_refresh_token(
    subject: uuid.UUID, token_type: TokenType
) -> tuple[str, uuid.UUID, datetime]:
    """Returns (token, jti, expires_at). The caller persists a
    RefreshToken row keyed by `jti` so the token can be looked up and
    revoked (logout, password reset) without decoding every stored
    session — see docs/Implementation Plan.md Phase 1.
    """
    now = datetime.now(UTC)
    jti = uuid.uuid4()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    claims = {
        "sub": str(subject),
        "type": token_type,
        "jti": str(jti),
        "iat": now,
        "exp": expires_at,
    }
    return _encode(claims), jti, expires_at


def decode_token(token: str, expected_types: TokenType | tuple[TokenType, ...]) -> dict[str, Any]:
    if isinstance(expected_types, str):
        expected_types = (expected_types,)

    try:
        claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AppError(
            status_code=401, code="UNAUTHENTICATED", message="Invalid or expired token."
        ) from exc

    if claims.get("type") not in expected_types:
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Invalid or expired token.")

    return claims
