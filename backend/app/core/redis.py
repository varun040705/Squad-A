"""
Redis client configuration.

Provides a singleton async Redis client for the application.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from redis.asyncio import Redis
from redis.asyncio import from_url

from app.core.config import settings

# Singleton Redis client
redis_client: Redis = from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    health_check_interval=30,
)


async def get_redis() -> AsyncIterator[Redis]:
    """
    FastAPI dependency that provides the shared Redis client.
    """
    yield redis_client


async def ping_redis() -> bool:
    """
    Verify Redis connectivity.

    Returns:
        True if Redis responds.

    Raises:
        redis.exceptions.RedisError
            If Redis is unavailable.
    """
    return await redis_client.ping()


async def close_redis() -> None:
    """
    Gracefully close the Redis connection pool.
    """
    await redis_client.aclose()