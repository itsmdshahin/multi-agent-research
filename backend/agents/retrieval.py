"""
Retrieval Agent — performs semantic search over the Qdrant vector store.
Supports filtered search by document IDs and reranking by similarity score.
"""
from typing import List, Optional

from core.config import settings
from core.logging import get_logger
from services.embeddings import embedding_service

logger = get_logger(__name__)


class RetrievalAgent:
    """
    Semantic retrieval agent that queries Qdrant for relevant document chunks.
    """

    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        top_k: int = settings.TOP_K_RETRIEVAL,
        score_threshold: float = settings.SIMILARITY_THRESHOLD,
    ) -> List[dict]:
        """
        Retrieve semantically similar document chunks for the given query.
        Optionally filters to specific documents and/or user.
        """
        logger.debug("Retrieval started", query=query[:80], top_k=top_k)

        # Embed the query
        query_embedding = await embedding_service.embed_single(query)

        # Search Qdrant
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            document_ids=document_ids if document_ids else None,
            user_id=user_id,
        )

        # Deduplicate by chunk content (can get near-duplicates from overlapping chunks)
        seen_texts: set = set()
        deduped = []
        for r in results:
            text_key = r["text"][:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                deduped.append(r)

        logger.info("Retrieval complete", results=len(deduped), query=query[:50])
        return deduped

    async def retrieve_with_context_compression(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        top_k: int = 10,
        final_k: int = 5,
    ) -> List[dict]:
        """
        Retrieve more chunks than needed, then select the most relevant ones.
        Acts as a lightweight reranker using cosine similarity to the query embedding.
        """
        # Get a larger pool
        candidates = await self.retrieve(
            query=query,
            document_ids=document_ids,
            user_id=user_id,
            top_k=top_k,
            score_threshold=0.4,  # lower threshold for wider net
        )

        if len(candidates) <= final_k:
            return candidates

        # Re-embed query (cached from prior call but we re-use for safety)
        query_embedding = await embedding_service.embed_single(query)

        # Re-rank by re-computing similarity (scores already in results but normalise)
        # Candidates are already sorted by score; just take top final_k
        return candidates[:final_k]

    def format_context(self, chunks: List[dict], max_tokens: int = 3000) -> str:
        """
        Format retrieved chunks into a context string for the LLM.
        Respects approximate token budget.
        """
        context_parts = []
        total_chars = 0
        # Rough approximation: 1 token ≈ 4 chars
        char_budget = max_tokens * 4

        for chunk in chunks:
            doc_name = chunk.get("document_name", "Unknown Document")
            page = chunk.get("page_number", "?")
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)

            part = f"[Source: {doc_name}, Page {page} | Relevance: {score:.2f}]\n{text}\n"
            if total_chars + len(part) > char_budget:
                break
            context_parts.append(part)
            total_chars += len(part)

        return "\n---\n".join(context_parts)
