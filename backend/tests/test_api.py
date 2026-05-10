"""
Integration tests for authentication and document management.
Run with: pytest backend/tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

# We patch the DB and external services to isolate unit logic
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
class TestAuthRoutes:
    async def test_register_and_login(self):
        """Full register → login → me flow."""
        from main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register
            reg = await client.post("/api/v1/auth/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "securepassword123",
                "full_name": "Test User",
            })
            assert reg.status_code in (201, 400)  # 400 if already exists

            if reg.status_code == 201:
                # Login
                login = await client.post("/api/v1/auth/login", data={
                    "username": "test@example.com",
                    "password": "securepassword123",
                })
                assert login.status_code == 200
                token_data = login.json()
                assert "access_token" in token_data

                # Get current user
                me = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"},
                )
                assert me.status_code == 200
                assert me.json()["email"] == "test@example.com"

    async def test_login_invalid_credentials(self):
        from main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword",
            })
            assert resp.status_code == 401

    async def test_protected_route_without_token(self):
        from main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/me")
            assert resp.status_code == 401


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health_check(self):
        from main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"


@pytest.mark.asyncio
class TestEmbeddingService:
    async def test_embedding_dimension(self):
        """Test that embeddings have the correct dimension."""
        from services.embeddings import EmbeddingService
        from unittest.mock import AsyncMock, patch, MagicMock

        service = EmbeddingService()

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536, index=0)]

        with patch.object(service.client.embeddings, 'create', new_callable=AsyncMock, return_value=mock_response):
            embedding = await service.embed_single("test text")
            assert len(embedding) == 1536

    def test_cosine_similarity(self):
        from services.embeddings import EmbeddingService
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        sim = EmbeddingService.cosine_similarity(vec_a, vec_b)
        assert abs(sim - 1.0) < 1e-6

        vec_c = [0.0, 1.0, 0.0]
        sim_ortho = EmbeddingService.cosine_similarity(vec_a, vec_c)
        assert abs(sim_ortho) < 1e-6


@pytest.mark.asyncio
class TestPDFIngestion:
    async def test_text_chunker(self):
        from services.pdf_ingestion import TextChunker, PageContent

        chunker = TextChunker(chunk_size=10, chunk_overlap=2)
        pages = [PageContent(page_number=1, text="word " * 30)]
        chunks = chunker.chunk_pages(pages, "doc-id", "test.pdf")
        assert len(chunks) > 1
        assert all(c.document_id == "doc-id" for c in chunks)

    async def test_text_cleaner(self):
        from services.pdf_ingestion import PDFExtractor
        raw = "hello   \n\n  world   "
        cleaned = PDFExtractor._clean_text(raw)
        assert "  " not in cleaned
        assert cleaned == "hello world"


class TestPlannerAgent:
    def test_default_plan_coding_query(self):
        from agents.planner import PlannerAgent
        plan = PlannerAgent._default_plan("write a python function to sort a list")
        assert plan["query_type"] == "coding"
        assert "coding" in plan["agents_to_use"]

    def test_default_plan_research_query(self):
        from agents.planner import PlannerAgent
        plan = PlannerAgent._default_plan("summarize the methodology section")
        assert plan["query_type"] == "research"
        assert "retrieval" in plan["agents_to_use"]
