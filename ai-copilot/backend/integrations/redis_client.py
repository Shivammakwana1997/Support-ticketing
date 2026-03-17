from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

_redis_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


class RedisClient:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        await self._redis.set(key, value, ex=ex)

    async def delete(self, key: str) -> int:
        return await self._redis.delete(key)

    async def publish(self, channel: str, message: str) -> int:
        return await self._redis.publish(channel, message)

    async def subscribe(self, *channels: str) -> aioredis.client.PubSub:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def lpush(self, key: str, *values: str) -> int:
        return await self._redis.lpush(key, *values)

    async def rpop(self, key: str) -> str | None:
        return await self._redis.rpop(key)

    async def brpop(self, key: str, timeout: int = 0) -> tuple[str, str] | None:
        return await self._redis.brpop(key, timeout=timeout)

    async def llen(self, key: str) -> int:
        return await self._redis.llen(key)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        await self._redis.setex(key, seconds, value)

    async def incr(self, key: str) -> int:
        return await self._redis.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        return await self._redis.expire(key, seconds)
