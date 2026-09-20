import json
from collections.abc import Awaitable, Callable
from typing import Any

from redis.exceptions import RedisError

from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


async def cache_get_or_set(key: str, ttl_seconds: int, loader: Callable[[], Awaitable[Any]]) -> Any:
    """Cache-aside helper for read-heavy, infrequently-changing public
    reads (SRS Part 3 §14: "Redis caching of catalog/category/homepage
    reads"). `loader` must return JSON-serializable data (the plain
    dicts/lists `success_envelope(data=...)` already wraps, not ORM
    objects) — cached with a TTL so a missed invalidation self-heals
    within that window instead of serving stale data indefinitely.

    Redis is a performance optimization here, not a source of truth
    (NFR-AVL-003): a read failing against it falls back to the DB
    loader instead of failing the whole request, and a write failing
    to populate the cache is swallowed the same way.
    """
    try:
        cached = await get_redis().get(key)
    except RedisError:
        logger.warning("cache_read_failed", key=key)
        return await loader()

    if cached is not None:
        return json.loads(cached)

    value = await loader()
    try:
        await get_redis().set(key, json.dumps(value), ex=ttl_seconds)
    except RedisError:
        logger.warning("cache_write_failed", key=key)
    return value


async def cache_delete(*keys: str) -> None:
    keys = tuple(k for k in keys if k)
    if not keys:
        return
    try:
        await get_redis().delete(*keys)
    except RedisError:
        logger.warning("cache_delete_failed", keys=keys)


async def cache_delete_prefix(prefix: str) -> None:
    """For keys that vary per parameter (e.g. one per product/category
    slug) where the write path can't enumerate every affected key."""
    redis = get_redis()
    try:
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match=f"{prefix}*", count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except RedisError:
        logger.warning("cache_invalidation_failed", prefix=prefix)
