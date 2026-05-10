"""
Pydantic v2 schemas for API request/response validation.
"""
import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ─────────────────────────── Auth Schemas ────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


# ─────────────────────────── Document Schemas ────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    status: str
    page_count: Optional[int]
    word_count: Optional[int]
    chunk_count: Optional[int]
    doc_meta: Optional[dict]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int


# ─────────────────────────── Conversation & Chat Schemas ────────────────────────────

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    document_ids: Optional[List[uuid.UUID]] = []


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    meta: Optional[dict]
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class Citation(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_number: int
    excerpt: str
    similarity_score: Optional[float] = None


class AgentActivity(BaseModel):
    agent: str
    action: str
    status: str  # running | done | error
    detail: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: Optional[List[Citation]] = []
    agent_logs: Optional[List[AgentActivity]] = []
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str
    document_ids: Optional[List[uuid.UUID]] = []  # filter to specific docs
    enable_web_search: bool = False
    model: Optional[str] = None  # override default model


class ChatResponse(BaseModel):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    content: str
    citations: List[Citation] = []
    agent_activities: List[AgentActivity] = []
    model_used: str
    token_count: Optional[int] = None


# ─────────────────────────── Report Schemas ────────────────────────────

class ReportCreate(BaseModel):
    title: str
    document_ids: List[uuid.UUID]
    prompt: Optional[str] = None
    report_type: str = "research_summary"


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    report_type: str
    content: Optional[str]
    markdown_content: Optional[str]
    status: str
    document_ids: Optional[list]
    created_at: datetime
    updated_at: datetime


# ─────────────────────────── Search Schemas ────────────────────────────

class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[uuid.UUID]] = []  # empty = search all user docs
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_number: int
    content: str
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


# ─────────────────────────── Agent Status ────────────────────────────

class AgentStatusEvent(BaseModel):
    """Server-Sent Event payload for streaming agent status."""
    event_type: str  # agent_start | agent_done | token | citation | error | done
    agent: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Any] = None
