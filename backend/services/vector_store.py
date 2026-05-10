"""
Qdrant vector database service for document embeddings and semantic search.
Handles collection management, upserting vectors, and hybrid search.
"""
import uuid
from typing import List, Optional, Tuple

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_qdrant_client: Optional[AsyncQdrantClient] = None


async def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=False,
        )
    return _qdrant_client


class VectorStore:
    """High-level abstraction over Qdrant for document chunk storage and retrieval."""

    def __init__(self, client: AsyncQdrantClient):
        self.client = client
        self.collection = settings.QDRANT_COLLECTION_NAME
        self.dim = settings.EMBEDDING_DIMENSION

    async def ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            await self.client.get_collection(self.collection)
            logger.debug("Qdrant collection exists", collection=self.collection)
        except (UnexpectedResponse, Exception):
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(
                    size=self.dim,
                    distance=qmodels.Distance.COSINE,
                ),
                optimizers_config=qmodels.OptimizersConfigDiff(
                    indexing_threshold=20000,
                ),
                hnsw_config=qmodels.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                ),
            )
            logger.info("Created Qdrant collection", collection=self.collection)

    async def upsert_chunks(
        self,
        document_id: str,
        user_id: str,
        chunks: List[dict],  # [{text, embedding, page, chunk_index, ...}]
    ) -> int:
        """Batch-upsert document chunks into Qdrant."""
        await self.ensure_collection()

        points = []
        for chunk in chunks:
            point_id = str(uuid.uuid4())
            payload = {
                "document_id": document_id,
                "user_id": user_id,
                "text": chunk["text"],
                "page_number": chunk.get("page_number", 0),
                "chunk_index": chunk.get("chunk_index", 0),
                "document_name": chunk.get("document_name", ""),
                "total_pages": chunk.get("total_pages", 0),
            }
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload=payload,
                )
            )

        # Batch upsert in groups of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await self.client.upsert(
                collection_name=self.collection,
                points=batch,
                wait=True,
            )

        logger.info("Upserted chunks", document_id=document_id, count=len(points))
        return len(points)

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = 0.5,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> List[dict]:
        """Semantic similarity search with optional filters."""
        await self.ensure_collection()

        filter_conditions = []

        if user_id:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=user_id),
                )
            )

        if document_ids:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(any=document_ids),
                )
            )

        query_filter = (
            qmodels.Filter(must=filter_conditions) if filter_conditions else None
        )

        results = await self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "score": hit.score,
                "document_id": hit.payload.get("document_id"),
                "document_name": hit.payload.get("document_name"),
                "text": hit.payload.get("text"),
                "page_number": hit.payload.get("page_number"),
                "chunk_index": hit.payload.get("chunk_index"),
            }
            for hit in results
        ]

    async def delete_document_chunks(self, document_id: str) -> None:
        """Remove all chunks belonging to a document."""
        await self.client.delete(
            collection_name=self.collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
        logger.info("Deleted document chunks from Qdrant", document_id=document_id)

    async def get_collection_info(self) -> dict:
        """Return basic collection statistics."""
        info = await self.client.get_collection(self.collection)
        return {
            "name": self.collection,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
