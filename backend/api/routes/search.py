"""
Search API route: semantic search across user documents.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from core.logging import get_logger
from database.session import get_db
from models.db_models import User
from models.schemas import SearchRequest, SearchResponse, SearchResult
from agents.retrieval import RetrievalAgent
from services.vector_store import VectorStore, get_qdrant_client

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search across the user's indexed documents.
    Returns ranked chunks with document name, page number and similarity score.
    """
    qdrant_client = await get_qdrant_client()
    vector_store = VectorStore(qdrant_client)
    retrieval = RetrievalAgent(vector_store)

    doc_id_strs = [str(did) for did in (payload.document_ids or [])]

    chunks = await retrieval.retrieve(
        query=payload.query,
        document_ids=doc_id_strs if doc_id_strs else None,
        user_id=str(current_user.id),
        top_k=payload.top_k,
        score_threshold=payload.similarity_threshold,
    )

    results = [
        SearchResult(
            document_id=uuid.UUID(c["document_id"]) if c.get("document_id") else uuid.uuid4(),
            document_name=c.get("document_name", "Unknown"),
            page_number=c.get("page_number", 0),
            content=c.get("text", ""),
            similarity_score=round(c.get("score", 0.0), 4),
        )
        for c in chunks
    ]

    return SearchResponse(
        query=payload.query,
        results=results,
        total=len(results),
    )
