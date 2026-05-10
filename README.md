# 🧠 Multi-Agent AI Research Assistant

> **Production-grade enterprise AI research platform** — upload PDFs, ask complex questions, and watch a fleet of specialized AI agents collaborate in real time to retrieve, reason, cite, and synthesize research-grade answers.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-blue)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Multi-PDF Chat** | Upload dozens of research papers and chat across all of them simultaneously |
| **Multi-Agent Orchestration** | 8 specialized AI agents working in parallel via LangGraph |
| **RAG Pipeline** | Qdrant vector search with hybrid retrieval, chunking, and context compression |
| **Citation Tracking** | Every answer includes source document name, page number, and relevance score |
| **Real-Time Streaming** | Token-by-token SSE streaming with live agent-activity panels |
| **Research Reports** | Generate AI-written summaries, comparisons, and technical deep-dives |
| **Web Search** | Blend uploaded document context with live Tavily web search |
| **Persistent Memory** | Redis short-term + PostgreSQL long-term conversation memory |
| **JWT Authentication** | Full register/login/refresh flow with protected routes |
| **PDF + OCR Support** | PyMuPDF extraction with pdfplumber + Tesseract OCR fallback |
| **Docker Deployment** | One-command `docker compose up` brings up all 5 services |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                  │
│  Landing · Dashboard · Chat · Documents · Reports         │
└─────────────────────────┬───────────────────────────────┘
                          │ SSE / REST
┌─────────────────────────▼───────────────────────────────┐
│              FastAPI API Gateway (Python 3.12)            │
│  /auth  /chat/stream  /documents  /reports                │
│  JWT Auth · Rate Limiting · CORS · GZip                   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│          LangGraph Multi-Agent Orchestrator               │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Planner  │→ │Retrieval │→ │Research  │→ │Citation │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Memory   │  │Web Search│  │  Coding  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────┴───────────────────────────────────────────────────┐
│  Infrastructure                                           │
│  Qdrant (vectors) · PostgreSQL (long-term) · Redis (cache)│
│  OpenAI API · Anthropic Claude API · Tavily Search        │
└──────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
User Query
    ↓
Planner Agent   ← decides which agents to invoke based on intent
    ↓
Memory Agent    ← loads relevant conversation history from Redis
    ↓
Retrieval Agent ← semantic search over Qdrant vector store
    ↓  (parallel)
Web Search Agent ← Tavily search (if enabled)
    ↓
Research Agent  ← synthesizes chunks + web results into answer
    ↓  (if code query)
Coding Agent    ← generates/explains code from document context
    ↓
Citation Agent  ← matches response to source chunks with page numbers
    ↓
Synthesizer     ← combines all outputs → saves to memory → streams response
```

---

## 📁 Project Structure

```
multi-agent-research/
│
├── backend/                          # Python FastAPI backend
│   ├── agents/                       # Individual agent implementations
│   │   ├── planner.py                # Intent classification + planning
│   │   ├── retrieval.py              # Qdrant semantic search
│   │   ├── research.py               # Document synthesis + reports
│   │   ├── coding.py                 # Code generation agent
│   │   ├── citation.py               # Source citation extraction
│   │   ├── web_search.py             # Tavily web search
│   │   └── memory.py                 # Redis/DB memory management
│   ├── api/routes/                   # FastAPI route handlers
│   │   ├── auth.py                   # Register, login, refresh, me
│   │   ├── chat.py                   # Conversations + SSE streaming
│   │   ├── documents.py              # Upload, list, delete, ingest
│   │   └── reports.py                # Generate, list, export reports
│   ├── core/                         # Cross-cutting concerns
│   │   ├── config.py                 # Pydantic settings (env vars)
│   │   ├── security.py               # JWT + bcrypt
│   │   ├── logging.py                # Structured logging (structlog)
│   │   └── middleware.py             # Rate limiting middleware
│   ├── database/                     # Database layer
│   │   ├── session.py                # Async SQLAlchemy engine + sessions
│   │   └── repositories.py           # CRUD repository pattern
│   ├── memory/
│   │   └── redis_memory.py           # Redis short-term memory cache
│   ├── models/
│   │   ├── db_models.py              # SQLAlchemy ORM models
│   │   └── schemas.py                # Pydantic request/response schemas
│   ├── services/
│   │   ├── embeddings.py             # OpenAI embedding service
│   │   ├── pdf_ingestion.py          # PyMuPDF + OCR + chunking
│   │   └── vector_store.py           # Qdrant vector operations
│   ├── workflows/
│   │   └── research_workflow.py      # LangGraph state machine
│   ├── alembic/                      # Database migrations
│   ├── tests/                        # Pytest test suite
│   │   ├── test_agents.py            # Unit tests for all agents
│   │   ├── test_api.py               # API route tests
│   │   └── test_routes.py            # Integration route tests
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic.ini
│   └── pytest.ini
│
├── frontend/                         # Next.js 15 frontend
│   └── src/
│       ├── app/                      # App Router pages
│       │   ├── page.tsx              # Landing page
│       │   ├── auth/                 # Login + Register
│       │   ├── dashboard/            # Main dashboard
│       │   ├── chat/                 # Conversations + [id] chat
│       │   ├── documents/            # Document manager
│       │   ├── reports/              # Research reports
│       │   └── settings/             # User settings
│       ├── components/
│       │   ├── layout/Sidebar.tsx    # Navigation sidebar
│       │   ├── chat/                 # MessageBubble, ChatInput, Citations
│       │   └── agents/               # AgentActivityPanel
│       ├── hooks/                    # useAuth, useStream, useDocumentPoller
│       ├── lib/
│       │   ├── api.ts                # Axios API client + interceptors
│       │   ├── utils.ts              # Helpers, formatters
│       │   └── stores/               # Zustand state stores
│       └── types/index.ts            # TypeScript types
│
├── docker/
│   └── nginx.conf                    # Nginx reverse proxy config
├── docker-compose.yml                # Full stack orchestration
├── .env.example                      # Environment template
├── Makefile                          # Dev/ops shortcuts
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2
- OpenAI API key (required)
- Anthropic API key (optional)
- Tavily API key (optional — for web search)

### 1. Clone & configure

```bash
git clone https://github.com/itsmdshahin/multi-agent-research.git
cd multi-agent-research

# Copy and edit environment variables
cp .env.example .env
```

Edit `.env` — the **required** values are:

```env
OPENAI_API_KEY=sk-...         # Required
SECRET_KEY=<random-256-bit>   # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

Optional but recommended:
```env
ANTHROPIC_API_KEY=sk-ant-...  # Enables Claude model
TAVILY_API_KEY=tvly-...       # Enables web search agent
```

### 2. Start everything

```bash
docker compose up -d --build
```

This starts 5 services:
| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |
| **PostgreSQL** | localhost:5432 |

### 3. Create your account

Open http://localhost:3000 → **Get started** → register → upload a PDF → start chatting.

---

## 🛠 Development Setup

```bash
# Install dependencies
make install

# Start infrastructure only
make up-deps

# Run backend with hot reload
make dev-backend

# Run frontend with hot reload (separate terminal)
make dev-frontend
```

### Database migrations

```bash
# Apply all migrations
make migrate

# Create new migration
make migrate-new MSG="add user preferences column"

# Rollback one migration
make migrate-down
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only (no external services needed)
make test-unit

# Integration tests (requires running services)
make test-integration

# With coverage report
make test-coverage
```

Test coverage includes:
- ✅ All 8 agents (Planner, Retrieval, Research, Coding, Citation, Web Search, Memory, Synthesizer)
- ✅ PDF chunking + text extraction
- ✅ Embedding service + cosine similarity
- ✅ JWT security (create, verify, tamper detection)
- ✅ Redis memory cache operations
- ✅ All API route authentication guards
- ✅ File upload validation

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create new account |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET`  | `/api/v1/auth/me` | Get current user |

### Documents

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/documents/upload` | Upload PDF (triggers background ingestion) |
| `GET`  | `/api/v1/documents/` | List user's documents |
| `GET`  | `/api/v1/documents/{id}` | Get document details |
| `DELETE` | `/api/v1/documents/{id}` | Delete document + vectors |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/conversations` | Create conversation |
| `GET`  | `/api/v1/chat/conversations` | List conversations |
| `GET`  | `/api/v1/chat/conversations/{id}/messages` | Get message history |
| `POST` | `/api/v1/chat/stream` | **Send message (SSE streaming)** |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete conversation |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/reports/` | Generate research report |
| `GET`  | `/api/v1/reports/` | List reports |
| `GET`  | `/api/v1/reports/{id}` | Get report |
| `GET`  | `/api/v1/reports/{id}/export/markdown` | Export as Markdown |
| `DELETE` | `/api/v1/reports/{id}` | Delete report |

### SSE Stream Event Format

The `/api/v1/chat/stream` endpoint emits `text/event-stream` events:

```
data: {"type": "agent_activity", "data": {"agent": "planner", "action": "Planning workflow", "status": "done"}}

data: {"type": "agent_activity", "data": {"agent": "retrieval", "action": "Searching documents", "status": "running", "detail": "3 chunks found"}}

data: {"type": "citations", "data": [{"document_name": "paper.pdf", "page_number": 12, "similarity_score": 0.94, "excerpt": "..."}]}

data: {"type": "response", "content": "Based on the paper, the methodology..."}

data: {"type": "done", "message_id": "uuid-here"}
```

---

## 🔧 Configuration

All configuration is via environment variables (see `.env.example`).

### Key settings

| Variable | Default | Description |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4o` | LLM for agents |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | `1000` | Words per document chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Chunks returned per query |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score |
| `MAX_FILE_SIZE_MB` | `50` | Max PDF upload size |
| `RATE_LIMIT_REQUESTS` | `100` | Requests per window |
| `RATE_LIMIT_PERIOD` | `60` | Window in seconds |

---

## 🐳 Docker Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | User data, conversations, documents metadata |
| `redis` | redis:7-alpine | 6379 | Short-term memory, session cache, rate limiting |
| `qdrant` | qdrant/qdrant | 6333/6334 | Document chunk vectors |
| `backend` | custom | 8000 | FastAPI + LangGraph agents |
| `frontend` | custom | 3000 | Next.js UI |

---

## 🤖 Agent Details

### Planner Agent
Uses GPT-4o to classify query intent and produce a JSON execution plan. Decides which downstream agents to invoke. Falls back to rule-based planning if LLM fails.

### Retrieval Agent
Embeds the query with `text-embedding-3-small`, queries Qdrant with cosine similarity, deduplicates overlapping chunks, applies context compression.

### Research Agent
Synthesizes retrieved chunks + web results into structured markdown answers. Supports single-doc Q&A, multi-doc comparison, and report generation.

### Coding Agent
Generates production-quality code from document context. Parses multiple code blocks (Python, TypeScript, SQL, etc.) from LLM output.

### Citation Agent
Matches LLM responses back to source chunks. Deduplicates by (document, page), filters low-relevance results, returns top 5 citations with page numbers and relevance scores.

### Memory Agent
Loads the last N messages from Redis for context injection. Saves each exchange back to Redis. Falls back gracefully if Redis is unavailable.

### Web Search Agent
Integrates Tavily API for real-time web results. Returns structured title/URL/content tuples that the Research agent can blend with document context.

---

## 🔒 Security

- **JWT** access tokens (1d) + refresh tokens (30d)
- **bcrypt** password hashing
- **Rate limiting** per IP via Redis sliding window
- **File validation** — only PDF, max 50MB
- **CORS** configured per environment
- **Non-root Docker user** for all containers
- **Environment variable** injection — no secrets in code

---

## 📦 Tech Stack

**Backend**
- Python 3.12 · FastAPI · Uvicorn
- LangGraph · LangChain · LangChain-OpenAI · LangChain-Anthropic
- SQLAlchemy (async) · Alembic · asyncpg
- Qdrant Client · Redis (aioredis)
- PyMuPDF · pdfplumber · pytesseract
- OpenAI · Anthropic · Tavily
- structlog · tenacity · python-jose · passlib

**Frontend**
- Next.js 15 · React 18 · TypeScript
- Tailwind CSS · Radix UI primitives
- Zustand · Axios · react-markdown
- react-syntax-highlighter · react-dropzone
- date-fns · js-cookie

**Infrastructure**
- PostgreSQL 16 · Redis 7 · Qdrant
- Docker · Docker Compose · Nginx

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Built with [LangGraph](https://langchain-ai.github.io/langgraph/), [FastAPI](https://fastapi.tiangolo.com), [Next.js](https://nextjs.org), [Qdrant](https://qdrant.tech), and the [OpenAI](https://openai.com) / [Anthropic](https://anthropic.com) APIs.
