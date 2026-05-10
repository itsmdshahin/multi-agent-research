"""
Chat API routes: create conversations, send messages with SSE streaming.
"""
import json
import uuid
from typing import Annotated, AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from core.logging import get_logger
from database.session import get_db
from memory.redis_memory import MemoryCache, get_redis
from models.db_models import Conversation, Message, MessageRole, User
from models.schemas import (
    ChatRequest, ChatResponse, ConversationCreate, ConversationResponse
)
from services.vector_store import VectorStore, get_qdrant_client
from workflows.research_workflow import MultiAgentWorkflow

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title,
        meta={"document_ids": [str(did) for did in (payload.document_ids or [])]},
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_archived: bool = False,
):
    query = select(Conversation).where(Conversation.user_id == current_user.id)
    if not include_archived:
        query = query.where(Conversation.is_archived == False)
    query = query.order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role.value,
            "content": m.content,
            "citations": m.citations,
            "agent_logs": m.agent_logs,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and receive a streaming SSE response.
    The agent workflow runs asynchronously and emits events as each agent completes.
    """
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == payload.conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message to DB
    user_msg = Message(
        conversation_id=conv.id,
        role=MessageRole.USER,
        content=payload.message,
    )
    db.add(user_msg)
    await db.flush()

    # Merge document IDs from conversation meta + request
    conv_doc_ids = [str(did) for did in (conv.meta or {}).get("document_ids", [])]
    req_doc_ids = [str(did) for did in (payload.document_ids or [])]
    all_doc_ids = list(set(conv_doc_ids + req_doc_ids))

    # Build workflow
    redis = await get_redis()
    memory_cache = MemoryCache(redis)
    qdrant_client = await get_qdrant_client()
    vector_store = VectorStore(qdrant_client)

    workflow = MultiAgentWorkflow(
        vector_store=vector_store,
        memory_cache=memory_cache,
        model=payload.model,
    )

    initial_state = {
        "user_query": payload.message,
        "conversation_id": str(conv.id),
        "user_id": str(current_user.id),
        "document_ids": all_doc_ids,
        "enable_web_search": payload.enable_web_search,
        "conversation_history": [],
        "plan": None,
        "retrieved_chunks": [],
        "web_search_results": [],
        "research_summary": None,
        "code_snippets": None,
        "citations": [],
        "final_response": None,
        "agent_activity": [],
        "error": None,
        "_model": payload.model or "",
    }

    async def event_stream() -> AsyncGenerator[str, None]:
        full_response = ""
        all_citations = []
        agent_activities = []

        try:
            async for event in workflow.stream_execute(initial_state):
                event_type = event.get("event_type")

                if event_type == "agent_activity":
                    activity = event.get("data", {})
                    agent_activities.append(activity)
                    yield f"data: {json.dumps({'type': 'agent_activity', 'data': activity})}\n\n"

                elif event_type == "citations":
                    all_citations = event.get("data", [])
                    yield f"data: {json.dumps({'type': 'citations', 'data': all_citations})}\n\n"

                elif event_type == "response":
                    full_response = event.get("content", "")
                    yield f"data: {json.dumps({'type': 'response', 'content': full_response})}\n\n"

                elif event_type == "done":
                    # Persist assistant message
                    async with db:
                        assistant_msg = Message(
                            conversation_id=conv.id,
                            role=MessageRole.ASSISTANT,
                            content=full_response,
                            citations=all_citations,
                            agent_logs=agent_activities,
                        )
                        db.add(assistant_msg)

                        # Update conversation title if first message
                        if not conv.title or conv.title == "New Conversation":
                            conv.title = payload.message[:60] + ("..." if len(payload.message) > 60 else "")
                        await db.flush()

                    yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id)})}\n\n"

        except Exception as e:
            logger.error("Stream error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
