"""
Document management API routes: upload, list, get, delete.
Handles PDF ingestion in the background via FastAPI BackgroundTasks.
"""
import os
import uuid
from typing import Annotated, List, Optional

import aiofiles
from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException,
    Query, UploadFile, status
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from core.config import settings
from core.logging import get_logger
from database.session import get_db, get_db_context
from memory.redis_memory import get_redis, MemoryCache
from models.db_models import Document, DocumentStatus, User
from models.schemas import DocumentListResponse, DocumentResponse
from services.pdf_ingestion import pdf_ingestion_service
from services.vector_store import VectorStore, get_qdrant_client

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


async def get_vector_store() -> VectorStore:
    client = await get_qdrant_client()
    return VectorStore(client)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF document and queue it for ingestion."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    doc_id = uuid.uuid4()
    safe_filename = f"{doc_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # Save file to disk
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)

    # Create database record
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type="application/pdf",
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Queue background ingestion
    background_tasks.add_task(
        _ingest_document_background,
        str(doc.id),
        file_path,
        file.filename,
        str(current_user.id),
    )

    logger.info("Document upload queued", doc_id=str(doc.id), filename=file.filename)
    return doc


async def _ingest_document_background(
    document_id: str,
    file_path: str,
    document_name: str,
    user_id: str,
) -> None:
    """Background task: ingest PDF and update status in DB."""
    async with get_db_context() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        try:
            doc.status = DocumentStatus.PROCESSING
            await db.flush()

            # Get vector store
            qdrant_client = await get_qdrant_client()
            vector_store = VectorStore(qdrant_client)

            # Run ingestion
            ingestion_result = await pdf_ingestion_service.ingest(
                file_path=file_path,
                document_id=document_id,
                document_name=document_name,
                user_id=user_id,
                vector_store=vector_store,
            )

            # Update document record
            doc.status = DocumentStatus.READY
            doc.page_count = ingestion_result["page_count"]
            doc.word_count = ingestion_result["word_count"]
            doc.chunk_count = ingestion_result["chunk_count"]
            doc.doc_meta = ingestion_result["doc_meta"]
            doc.collection_name = settings.QDRANT_COLLECTION_NAME
            doc.extraction_meta = {"has_ocr": ingestion_result.get("has_ocr_pages", False)}
            await db.flush()

            logger.info("Document ingestion complete", document_id=document_id)

        except Exception as e:
            logger.error("Document ingestion failed", document_id=document_id, error=str(e))
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            await db.flush()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents belonging to the current user."""
    query = select(Document).where(Document.user_id == current_user.id)

    if status:
        query = query.where(Document.status == status)

    query = query.order_by(Document.created_at.desc())

    # Count total
    from sqlalchemy import func, select as sa_select
    count_query = sa_select(func.count()).select_from(
        select(Document).where(Document.user_id == current_user.id).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=list(documents),
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from Qdrant
    try:
        qdrant_client = await get_qdrant_client()
        vector_store = VectorStore(qdrant_client)
        await vector_store.delete_document_chunks(str(document_id))
    except Exception as e:
        logger.warning("Failed to delete from Qdrant", error=str(e))

    # Remove file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        logger.warning("Failed to delete file", error=str(e))

    await db.delete(doc)
