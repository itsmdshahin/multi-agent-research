"""
Redis client for short-term memory, session caching, and rate limiting.
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return a singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


class MemoryCache:
    """High-level Redis operations for the memory agent."""

    def __init__(self, client: aioredis.Redis):
        self.client = client

    async def set(self, key: str, value: Any, ttl: int = settings.REDIS_TTL_SECONDS) -> None:
        serialized = json.dumps(value, default=str)
        await self.client.setex(key, ttl, serialized)

    async def get(self, key: str) -> Optional[Any]:
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def append_to_list(self, key: str, value: Any, max_len: int = 50) -> None:
        """Append to a Redis list and trim to max_len (for conversation history)."""
        serialized = json.dumps(value, default=str)
        await self.client.rpush(key, serialized)
        await self.client.ltrim(key, -max_len, -1)

    async def get_list(self, key: str) -> list:
        """Retrieve all items in a Redis list."""
        items = await self.client.lrange(key, 0, -1)
        return [json.loads(item) for item in items]

    async def increment(self, key: str, ttl: int = 60) -> int:
        """Atomic increment for rate limiting."""
        pipe = self.client.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]

    # ── Conversation memory helpers ──

    def _conv_key(self, conversation_id: str) -> str:
        return f"conv:history:{conversation_id}"

    def _session_key(self, user_id: str) -> str:
        return f"session:{user_id}"

    async def save_message(self, conversation_id: str, role: str, content: str, meta: dict = None) -> None:
        entry = {"role": role, "content": content, "meta": meta or {}}
        await self.append_to_list(self._conv_key(conversation_id), entry)

    async def get_conversation_history(self, conversation_id: str) -> list:
        return await self.get_list(self._conv_key(conversation_id))

    async def clear_conversation(self, conversation_id: str) -> None:
        await self.delete(self._conv_key(conversation_id))

    async def save_user_session(self, user_id: str, data: dict) -> None:
        await self.set(self._session_key(user_id), data, ttl=3600)

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        return await self.get(self._session_key(user_id))
