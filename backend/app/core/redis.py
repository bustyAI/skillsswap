"""Redis connection management for rate limiting and caching."""

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import get_settings

_redis_client: redis.Redis | None = None


async def init_redis() -> None:
    """Initialize the Redis connection pool. Call once at app startup."""
    global _redis_client
    settings = get_settings()
    _redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close the Redis connection pool. Call once at app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def get_redis_client() -> redis.Redis:
    """Get the Redis client. Raises if not initialized."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_client


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency that provides a Redis client."""
    yield get_redis_client()


RedisClient = Annotated[redis.Redis, Depends(get_redis)]
