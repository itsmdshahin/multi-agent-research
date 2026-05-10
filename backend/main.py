"""
Multi-Agent AI Research Assistant — FastAPI Application Entry Point.

Configures middleware, mounts routers, handles startup/shutdown lifecycle.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.logging import get_logger, setup_logging
from core.middleware import RateLimitMiddleware
from database.session import create_all_tables
from memory.redis_memory import close_redis, get_redis
from services.vector_store import VectorStore, get_qdrant_client

# Import routers
from api.routes.auth import router as auth_router
from api.routes.documents import router as documents_router
from api.routes.chat import router as chat_router
from api.routes.reports import router as reports_router
from api.routes.search import router as search_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting Multi-Agent AI Research Assistant", version=settings.APP_VERSION)

    # Initialize database tables
    await create_all_tables()

    # Warm up Redis connection
    await get_redis()
    logger.info("Redis connected")

    # Warm up Qdrant and ensure collection exists
    try:
        qdrant_client = await get_qdrant_client()
        vs = VectorStore(qdrant_client)
        await vs.ensure_collection()
        logger.info("Qdrant connected and collection verified")
    except Exception as e:
        logger.warning("Qdrant connection failed at startup", error=str(e))

    logger.info("Application startup complete")
    yield

    # Cleanup
    await close_redis()
    logger.info("Application shutdown complete")


# ─────────────────────────── App Instance ────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Multi-Agent AI Research Assistant with RAG, PDF ingestion, and LangGraph orchestration.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─────────────────────────── Middleware ────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Log request duration for all endpoints."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.debug(
        "Request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    return response


# ─────────────────────────── Routers ────────────────────────────

API_PREFIX = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)


# ─────────────────────────── Health Endpoints ────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health():
    """Detailed health check for load balancers and monitoring."""
    checks = {}

    # Redis check
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    # Qdrant check
    try:
        qdrant_client = await get_qdrant_client()
        vs = VectorStore(qdrant_client)
        info = await vs.get_collection_info()
        checks["qdrant"] = f"healthy ({info.get('points_count', 0)} vectors)"
    except Exception as e:
        checks["qdrant"] = f"unhealthy: {e}"

    overall = "healthy" if all("healthy" in v for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "checks": checks,
    }


# ─────────────────────────── Exception Handlers ────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again."},
    )
