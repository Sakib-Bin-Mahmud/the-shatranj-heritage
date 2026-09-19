from collections.abc import Callable

from fastapi import Request

from app.core.redis import get_redis
from app.core.responses import AppError


def rate_limit(key: str, limit: int, window_seconds: int) -> Callable:
    """Fixed-window rate limiter dependency, per NFR-SEC-006.

    Applied to the auth endpoints docs/API Specification.md §2 ("Rate
    Limiting") names as rate-limited (login, register, forgot-password),
    plus admin login, password reset, checkout quoting, and order
    placement — added in Phase 8's rate-limiting review, since an
    unauthenticated or guest-accessible write endpoint left unlimited is
    a DoS/abuse surface regardless of whether the spec calls it "auth".
    Keyed by client IP + `key` so each endpoint has its own budget.
    """

    async def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        redis_key = f"rate_limit:{key}:{client_host}"
        redis = get_redis()

        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, window_seconds)

        if count > limit:
            raise AppError(
                status_code=429,
                code="RATE_LIMITED",
                message="Too many requests. Please try again later.",
            )

    return dependency
