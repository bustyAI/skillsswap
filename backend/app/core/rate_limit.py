"""Rate limiting using Redis INCR + EXPIRE pattern."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.redis import get_redis


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


async def check_rate_limit(
    redis: Redis,
    key: str,
    limit: int,
    window_seconds: int,
) -> int:
    """Check and increment rate limit counter.

    Args:
        redis: Redis client
        key: Unique key for this rate limit (e.g., "ratelimit:recommendations:{user_id}")
        limit: Maximum allowed requests in the window
        window_seconds: Time window in seconds

    Returns:
        Current count after increment

    Raises:
        RateLimitExceeded: If limit is exceeded
    """
    current: int = await redis.incr(key)

    if current == 1:
        await redis.expire(key, window_seconds)

    if current > limit:
        ttl: int = await redis.ttl(key)
        raise RateLimitExceeded(retry_after=max(ttl, 1))

    return current


def rate_limit_dependency(
    key_prefix: str,
    limit: int,
    window_seconds: int = 60,
) -> Callable[[Request, Redis], Awaitable[None]]:
    """Factory for creating rate limit dependencies.

    Args:
        key_prefix: Prefix for the Redis key (e.g., "recommendations")
        limit: Maximum requests allowed per window
        window_seconds: Window duration in seconds (default: 60)

    Returns:
        A FastAPI dependency that enforces the rate limit

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            _: None = Depends(rate_limit_dependency("myendpoint", 10, 60)),
            user: TokenClaims = Depends(get_current_user),
        ):
            ...
    """

    async def dependency(
        request: Request,
        redis: Annotated[Redis, Depends(get_redis)],
    ) -> None:
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            identifier = request.client.host if request.client else "unknown"
        else:
            identifier = str(user_id)

        key = f"ratelimit:{key_prefix}:{identifier}"

        try:
            await check_rate_limit(redis, key, limit, window_seconds)
        except RateLimitExceeded as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(e.retry_after)},
            ) from e

    return dependency


class RateLimiter:
    """Rate limiter that can be used with authenticated user context.

    This version extracts user_id from TokenClaims rather than request.state,
    making it more explicit for authenticated endpoints.
    """

    def __init__(self, key_prefix: str, limit: int, window_seconds: int = 60) -> None:
        self.key_prefix = key_prefix
        self.limit = limit
        self.window_seconds = window_seconds

    async def check(self, redis: Redis, user_id: str) -> None:
        """Check rate limit for a specific user.

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        key = f"ratelimit:{self.key_prefix}:{user_id}"

        try:
            await check_rate_limit(redis, key, self.limit, self.window_seconds)
        except RateLimitExceeded as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(e.retry_after)},
            ) from e
