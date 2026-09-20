from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    """Process-wide async Redis client, reused across requests.

    Backs the rate limiter (NFR-SEC-006) now; catalog/session caching
    (SRS Part 3 §14) reuses the same client from later phases.
    """
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)
