"""
Embedding service: generate text embeddings via OpenAI.
Includes retry logic and batching for large documents.
"""
import asyncio
from typing import List

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_openai_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


class EmbeddingService:
    """Generates and manages text embeddings via OpenAI."""

    def __init__(self):
        self.client = get_openai_client()
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.max_batch_size = 100  # OpenAI allows up to 2048 but we keep it conservative

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        # Truncate to model's max token limit
        text = text[:8191]
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        Automatically splits into sub-batches to respect API limits.
        """
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i : i + self.max_batch_size]
            # Truncate each text
            batch = [t[:8191] for t in batch]

            embeddings = await self._embed_batch_raw(batch)
            all_embeddings.extend(embeddings)

            # Brief pause between batches to avoid rate limits
            if i + self.max_batch_size < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _embed_batch_raw(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        import math
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
        mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


# Singleton instance
embedding_service = EmbeddingService()
