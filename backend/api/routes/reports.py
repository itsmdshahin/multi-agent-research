"""
Reports API routes: generate, list, get, and export research reports.
"""
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from core.logging import get_logger
from database.session import get_db, get_db_context
from memory.redis_memory import MemoryCache, get_redis
from models.db_models import Document, Report, ReportStatus, User
from models.schemas import ReportCreate, ReportResponse
from services.vector_store import VectorStore, get_qdrant_client
from agents.research import ResearchAgent
from agents.retrieval import RetrievalAgent
from langchain_openai import ChatOpenAI
from core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    payload: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new research report from uploaded documents."""
    # Verify documents belong to user
    for doc_id in payload.document_ids:
        result = await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.user_id == current_user.id,
                Document.status == "ready",
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"Document {doc_id} not found or not ready"
            )

    report = Report(
        user_id=current_user.id,
        title=payload.title,
        report_type=payload.report_type,
        document_ids=[str(did) for did in payload.document_ids],
        prompt=payload.prompt,
        status=ReportStatus.GENERATING,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    background_tasks.add_task(
        _generate_report_background,
        str(report.id),
        str(current_user.id),
        payload.title,
        [str(did) for did in payload.document_ids],
        payload.prompt,
        payload.report_type,
    )

    return report


async def _generate_report_background(
    report_id: str,
    user_id: str,
    title: str,
    document_ids: List[str],
    prompt: str,
    report_type: str,
) -> None:
    """Background task to generate the report content."""
    async with get_db_context() as db:
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return

        try:
            qdrant_client = await get_qdrant_client()
            vector_store = VectorStore(qdrant_client)
            retrieval = RetrievalAgent(vector_store)

            # Retrieve context from all documents
            combined_query = prompt or f"Provide a comprehensive {report_type} of these documents"
            chunks = await retrieval.retrieve(
                query=combined_query,
                document_ids=document_ids,
                user_id=user_id,
                top_k=20,  # More chunks for report generation
                score_threshold=0.3,
            )

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
                max_tokens=4096,
            )
            research_agent = ResearchAgent(llm)

            markdown_content = await research_agent.generate_report(
                title=title,
                document_ids=document_ids,
                prompt=prompt,
                chunks=chunks,
                report_type=report_type,
            )

            report.markdown_content = markdown_content
            report.content = markdown_content  # also store as plain content
            report.status = ReportStatus.READY
            await db.flush()

            logger.info("Report generated", report_id=report_id)

        except Exception as e:
            logger.error("Report generation failed", report_id=report_id, error=str(e))
            report.status = ReportStatus.FAILED
            await db.flush()


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/export/markdown", response_class=PlainTextResponse)
async def export_report_markdown(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report or not report.markdown_content:
        raise HTTPException(status_code=404, detail="Report or content not found")

    return PlainTextResponse(
        content=report.markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{report.title}.md"'},
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
