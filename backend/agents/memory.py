"""
Memory Agent — manages short-term (Redis) and long-term (PostgreSQL) memory.
Retrieves relevant conversation history and persists new exchanges.
"""
from typing import List, Optional

from core.logging import get_logger

logger = get_logger(__name__)


class MemoryAgent:
    def __init__(self, memory_cache):
        self.cache = memory_cache  # MemoryCache instance

    async def get_relevant_history(
        self,
        conversation_id: str,
        current_query: str,
        max_messages: int = 6,
    ) -> List[dict]:
        """
        Retrieve recent conversation history from Redis.
        Returns the last N messages (alternating user/assistant pairs).
        """
        try:
            history = await self.cache.get_conversation_history(conversation_id)
            # Return last max_messages entries
            return history[-max_messages:] if len(history) > max_messages else history
        except Exception as e:
            logger.warning("Failed to load memory", error=str(e))
            return []

    async def save_exchange(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Persist a user/assistant exchange to Redis memory."""
        try:
            await self.cache.save_message(conversation_id, "user", user_message)
            await self.cache.save_message(conversation_id, "assistant", assistant_message)
        except Exception as e:
            logger.warning("Failed to save memory", error=str(e))

    async def get_user_context(self, user_id: str) -> Optional[dict]:
        """Load user preferences and session from Redis."""
        try:
            return await self.cache.get_user_session(user_id)
        except Exception:
            return None

    async def update_user_context(self, user_id: str, data: dict) -> None:
        """Update user session data."""
        try:
            existing = await self.get_user_context(user_id) or {}
            existing.update(data)
            await self.cache.save_user_session(user_id, existing)
        except Exception as e:
            logger.warning("Failed to update user context", error=str(e))
