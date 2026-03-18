from __future__ import annotations

from collections.abc import AsyncGenerator

from integrations.redis_client import RedisClient, get_redis_pool


async def get_redis() -> AsyncGenerator[RedisClient, None]:
    pool = await get_redis_pool()
    yield RedisClient(pool)
