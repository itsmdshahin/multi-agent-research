"""
Web Search Agent — fetches real-time information from the internet.
Supports Tavily API with graceful fallback.
"""
from typing import List, Optional

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class WebSearchAgent:
    def __init__(self):
        self.tavily_client = None
        if settings.TAVILY_API_KEY:
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            except ImportError:
                logger.warning("Tavily package not installed")

    async def search(self, query: str, num_results: int = 5) -> List[dict]:
        """Search the web and return structured results."""
        if self.tavily_client:
            return await self._tavily_search(query, num_results)

        logger.warning("No web search provider configured, returning empty results")
        return []

    async def _tavily_search(self, query: str, num_results: int) -> List[dict]:
        """Search using Tavily API."""
        import asyncio
        try:
            # Tavily is sync; run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.tavily_client.search(
                    query=query,
                    max_results=num_results,
                    include_answer=True,
                    include_raw_content=False,
                )
            )

            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                })
            return results
        except Exception as e:
            logger.error("Tavily search failed", error=str(e))
            return []
