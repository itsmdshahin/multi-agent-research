"""
Integration tests for FastAPI routes.
Requires a running PostgreSQL, Redis and Qdrant or mocked versions.
Run with: pytest tests/test_routes.py -v -m integration
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Return a test client with all external deps mocked."""
    with (
        patch("database.session.create_all_tables", new_callable=AsyncMock),
        patch("memory.redis_memory.get_redis", new_callable=AsyncMock),
        patch("services.vector_store.get_qdrant_client", new_callable=AsyncMock),
    ):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c


@pytest.fixture
async def auth_headers(client):
    """Register a test user and return Bearer token headers."""
    uid = str(uuid.uuid4())[:8]
    email = f"test_{uid}@example.com"
    username = f"testuser_{uid}"

    with patch("api.routes.auth.get_db") as mock_db_dep:
        # Mock the DB session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        from models.db_models import User
        from core.security import get_password_hash
        mock_user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
        )
        mock_session.refresh = AsyncMock(return_value=mock_user)
        mock_db_dep.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_dep.return_value.__aexit__ = AsyncMock(return_value=False)

        from core.security import create_access_token
        token = create_access_token(str(mock_user.id))
        return {"Authorization": f"Bearer {token}", "_user": mock_user}


# ─── Health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
class TestHealthEndpoints:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_health_returns_status_field(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "status" in data
        assert data["status"] == "healthy"

    async def test_health_returns_version(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "version" in data


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
class TestAuthRoutes:
    async def test_register_missing_fields_422(self, client):
        resp = await client.post("/api/v1/auth/register", json={"email": "bad"})
        assert resp.status_code == 422

    async def test_login_wrong_credentials_401(self, client):
        with patch("api.routes.auth.get_db") as mock_db_dep:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
            )
            mock_db_dep.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_dep.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.post("/api/v1/auth/login", data={
                "username": "nobody@example.com",
                "password": "wrongpass",
            })
            assert resp.status_code == 401

    async def test_me_without_token_401(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_with_valid_token_200(self, client):
        import uuid as _uuid
        from core.security import create_access_token
        from models.db_models import User

        user_id = _uuid.uuid4()
        token = create_access_token(str(user_id))
        mock_user = User(id=user_id, email="me@example.com", username="me", hashed_password="x", is_active=True)

        with patch("api.routes.auth.get_db") as mock_db_dep:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user))
            )
            mock_db_dep.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_dep.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json()["email"] == "me@example.com"


# ─── Document Routes ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
class TestDocumentRoutes:
    async def test_list_documents_requires_auth(self, client):
        resp = await client.get("/api/v1/documents/")
        assert resp.status_code == 401

    async def test_upload_requires_auth(self, client):
        resp = await client.post("/api/v1/documents/upload", files={"file": ("test.pdf", b"data", "application/pdf")})
        assert resp.status_code == 401

    async def test_upload_rejects_non_pdf(self, client):
        import uuid as _uuid
        from core.security import create_access_token
        from models.db_models import User

        user_id = _uuid.uuid4()
        token = create_access_token(str(user_id))
        mock_user = User(id=user_id, email="x@x.com", username="x", hashed_password="x", is_active=True)

        with patch("api.routes.documents.get_current_user", return_value=mock_user):
            resp = await client.post(
                "/api/v1/documents/upload",
                files={"file": ("document.txt", b"text content", "text/plain")},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 400
            assert "PDF" in resp.json()["detail"]


# ─── Report Routes ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
class TestReportRoutes:
    async def test_list_reports_requires_auth(self, client):
        resp = await client.get("/api/v1/reports/")
        assert resp.status_code == 401

    async def test_create_report_requires_documents(self, client):
        import uuid as _uuid
        from core.security import create_access_token
        from models.db_models import User

        user_id = _uuid.uuid4()
        token = create_access_token(str(user_id))
        mock_user = User(id=user_id, email="r@r.com", username="reporter", hashed_password="x", is_active=True)

        with patch("api.routes.reports.get_current_user", return_value=mock_user):
            with patch("api.routes.reports.get_db") as mock_db_dep:
                mock_session = AsyncMock()
                # Document not found
                mock_session.execute = AsyncMock(
                    return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
                )
                mock_db_dep.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_db_dep.return_value.__aexit__ = AsyncMock(return_value=False)

                resp = await client.post(
                    "/api/v1/reports/",
                    json={"title": "Test Report", "document_ids": [str(_uuid.uuid4())]},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 404
