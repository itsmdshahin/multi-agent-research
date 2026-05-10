"""
Unit tests for agents and core services.
These tests mock all external dependencies (OpenAI, Redis, Qdrant).
Run with: pytest tests/test_agents.py -v -m unit
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─────────────────────────── Planner Agent ────────────────────────────

class TestPlannerAgent:
    """Tests for the Planner agent's intent classification logic."""

    def test_default_plan_coding_keywords(self):
        from agents.planner import PlannerAgent
        for q in ["write a python function", "implement this algorithm", "debug this code"]:
            plan = PlannerAgent._default_plan(q)
            assert plan["query_type"] == "coding", f"Failed for: {q}"
            assert "coding" in plan["agents_to_use"]

    def test_default_plan_research_keywords(self):
        from agents.planner import PlannerAgent
        for q in ["summarize the paper", "what are the findings", "compare methodologies"]:
            plan = PlannerAgent._default_plan(q)
            assert plan["query_type"] == "research"
            assert "retrieval" in plan["agents_to_use"]
            assert "citation" in plan["agents_to_use"]

    def test_default_plan_web_search_keywords(self):
        from agents.planner import PlannerAgent
        plan = PlannerAgent._default_plan("what is the latest research on transformers")
        assert plan["needs_web_search"] is True
        assert "web_search" in plan["agents_to_use"]

    def test_default_plan_always_includes_retrieval(self):
        from agents.planner import PlannerAgent
        plan = PlannerAgent._default_plan("explain the methodology")
        assert "retrieval" in plan["agents_to_use"]

    def test_default_plan_complexity_field(self):
        from agents.planner import PlannerAgent
        plan = PlannerAgent._default_plan("anything")
        assert plan["complexity"] in ("simple", "medium", "complex")

    @pytest.mark.asyncio
    async def test_plan_falls_back_on_json_error(self):
        from agents.planner import PlannerAgent

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="NOT VALID JSON {{{{"))

        agent = PlannerAgent(mock_llm)
        plan = await agent.plan("test query", [], [])
        # Should not raise — returns default plan
        assert "agents_to_use" in plan
        assert "query_type" in plan

    @pytest.mark.asyncio
    async def test_plan_parses_valid_llm_response(self):
        from agents.planner import PlannerAgent
        import json

        expected = {
            "query_type": "research",
            "agents_to_use": ["retrieval", "research", "citation"],
            "sub_tasks": ["retrieve context", "synthesize"],
            "needs_web_search": False,
            "complexity": "medium",
        }
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps(expected)))

        agent = PlannerAgent(mock_llm)
        plan = await agent.plan("summarize this paper", ["doc-1"], [])
        assert plan["query_type"] == "research"
        assert "retrieval" in plan["agents_to_use"]


# ─────────────────────────── Citation Agent ────────────────────────────

class TestCitationAgent:
    @pytest.mark.asyncio
    async def test_extract_returns_empty_for_no_chunks(self):
        from agents.citation import CitationAgent
        agent = CitationAgent(MagicMock())
        citations = await agent.extract("some response", [])
        assert citations == []

    @pytest.mark.asyncio
    async def test_extract_deduplicates_by_doc_page(self):
        from agents.citation import CitationAgent
        chunks = [
            {"document_id": "doc-1", "document_name": "paper.pdf", "page_number": 3, "text": "text a", "score": 0.9},
            {"document_id": "doc-1", "document_name": "paper.pdf", "page_number": 3, "text": "text b", "score": 0.85},
            {"document_id": "doc-1", "document_name": "paper.pdf", "page_number": 5, "text": "text c", "score": 0.8},
        ]
        agent = CitationAgent(MagicMock())
        citations = await agent.extract("response text", chunks)
        pages = [c["page_number"] for c in citations]
        assert len(pages) == len(set(pages)), "Duplicate pages found"

    @pytest.mark.asyncio
    async def test_extract_filters_low_score(self):
        from agents.citation import CitationAgent
        chunks = [
            {"document_id": "doc-1", "document_name": "paper.pdf", "page_number": 1, "text": "text", "score": 0.3},
        ]
        agent = CitationAgent(MagicMock())
        citations = await agent.extract("response", chunks)
        assert len(citations) == 0

    @pytest.mark.asyncio
    async def test_extract_limits_to_five(self):
        from agents.citation import CitationAgent
        chunks = [
            {"document_id": f"doc-{i}", "document_name": f"paper{i}.pdf", "page_number": i, "text": "x", "score": 0.9}
            for i in range(10)
        ]
        agent = CitationAgent(MagicMock())
        citations = await agent.extract("response", chunks)
        assert len(citations) <= 5

    def test_format_inline_citations_empty(self):
        from agents.citation import CitationAgent
        result = CitationAgent.format_inline_citations("Hello world", [])
        assert result == "Hello world"

    def test_format_inline_citations_appends_footer(self):
        from agents.citation import CitationAgent
        citations = [{"document_name": "paper.pdf", "page_number": 3, "similarity_score": 0.9}]
        result = CitationAgent.format_inline_citations("Answer", citations)
        assert "Sources" in result
        assert "paper.pdf" in result
        assert "Page 3" in result


# ─────────────────────────── PDF Ingestion ────────────────────────────

class TestTextChunker:
    def test_chunks_basic_text(self):
        from services.pdf_ingestion import TextChunker, PageContent
        chunker = TextChunker(chunk_size=10, chunk_overlap=2)
        pages = [PageContent(page_number=1, text=" ".join([f"word{i}" for i in range(30)]))]
        chunks = chunker.chunk_pages(pages, "doc-id", "test.pdf")
        assert len(chunks) > 1
        assert all(c.document_id == "doc-id" for c in chunks)
        assert all(c.document_name == "test.pdf" for c in chunks)

    def test_chunks_have_correct_page_number(self):
        from services.pdf_ingestion import TextChunker, PageContent
        chunker = TextChunker(chunk_size=5, chunk_overlap=1)
        pages = [
            PageContent(page_number=1, text="word " * 10),
            PageContent(page_number=2, text="word " * 10),
        ]
        chunks = chunker.chunk_pages(pages, "doc", "doc.pdf")
        page_nums = {c.page_number for c in chunks}
        assert 1 in page_nums
        assert 2 in page_nums

    def test_empty_pages_skipped(self):
        from services.pdf_ingestion import TextChunker, PageContent
        chunker = TextChunker()
        pages = [PageContent(page_number=1, text=""), PageContent(page_number=2, text="   ")]
        chunks = chunker.chunk_pages(pages, "doc", "doc.pdf")
        assert chunks == []

    def test_chunk_overlap_creates_continuity(self):
        from services.pdf_ingestion import TextChunker, PageContent
        chunker = TextChunker(chunk_size=5, chunk_overlap=3)
        words = ["a", "b", "c", "d", "e", "f", "g", "h"]
        pages = [PageContent(page_number=1, text=" ".join(words))]
        chunks = chunker.chunk_pages(pages, "doc", "doc.pdf")
        # With overlap, later chunks should share words with earlier ones
        if len(chunks) >= 2:
            text1 = set(chunks[0].text.split())
            text2 = set(chunks[1].text.split())
            assert len(text1 & text2) > 0, "Chunks should overlap"

    def test_text_cleaner_strips_whitespace(self):
        from services.pdf_ingestion import PDFExtractor
        dirty = "hello   \n\n\t  world   "
        clean = PDFExtractor._clean_text(dirty)
        assert "  " not in clean
        assert clean == "hello world"

    def test_text_cleaner_removes_non_ascii(self):
        from services.pdf_ingestion import PDFExtractor
        text = "hello \x84 world"
        clean = PDFExtractor._clean_text(text)
        assert "\x84" not in clean


# ─────────────────────────── Embedding Service ────────────────────────────

class TestEmbeddingService:
    def test_cosine_similarity_identical_vectors(self):
        from services.embeddings import EmbeddingService
        vec = [1.0, 0.0, 0.0]
        assert abs(EmbeddingService.cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        from services.embeddings import EmbeddingService
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert abs(EmbeddingService.cosine_similarity(vec_a, vec_b)) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        from services.embeddings import EmbeddingService
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        assert abs(EmbeddingService.cosine_similarity(vec_a, vec_b) + 1.0) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        from services.embeddings import EmbeddingService
        assert EmbeddingService.cosine_similarity([0, 0], [1, 1]) == 0.0

    @pytest.mark.asyncio
    async def test_embed_single_calls_openai(self):
        from services.embeddings import EmbeddingService
        service = EmbeddingService()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536, index=0)]

        with patch.object(service.client.embeddings, "create", new_callable=AsyncMock, return_value=mock_response):
            result = await service.embed_single("test text")
            assert len(result) == 1536
            assert all(isinstance(v, float) for v in result)

    @pytest.mark.asyncio
    async def test_embed_batch_returns_correct_count(self):
        from services.embeddings import EmbeddingService
        service = EmbeddingService()

        def make_response(texts):
            mock = MagicMock()
            mock.data = [MagicMock(embedding=[0.1] * 1536, index=i) for i in range(len(texts))]
            return mock

        with patch.object(service.client.embeddings, "create", new_callable=AsyncMock,
                          side_effect=lambda **kw: make_response(kw["input"])):
            texts = ["text one", "text two", "text three"]
            results = await service.embed_batch(texts)
            assert len(results) == 3
            assert all(len(r) == 1536 for r in results)


# ─────────────────────────── Security ────────────────────────────

class TestSecurity:
    def test_password_hash_and_verify(self):
        from core.security import get_password_hash, verify_password
        password = "supersecret123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_create_and_decode_access_token(self):
        from core.security import create_access_token, decode_token
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        from core.security import create_refresh_token, decode_token
        token = create_refresh_token("user-456")
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises(self):
        from core.security import decode_token
        with pytest.raises(ValueError):
            decode_token("this.is.not.a.valid.jwt")

    def test_decode_tampered_token_raises(self):
        from core.security import create_access_token, decode_token
        token = create_access_token("user-789")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            decode_token(tampered)


# ─────────────────────────── Redis Memory ────────────────────────────

class TestMemoryCache:
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.setex = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.delete = AsyncMock()
        redis.exists = AsyncMock(return_value=False)
        redis.rpush = AsyncMock()
        redis.ltrim = AsyncMock()
        redis.lrange = AsyncMock(return_value=[])
        return redis

    @pytest.mark.asyncio
    async def test_set_and_get(self, mock_redis):
        from memory.redis_memory import MemoryCache
        import json
        cache = MemoryCache(mock_redis)
        mock_redis.get.return_value = json.dumps({"key": "value"})
        await cache.set("test-key", {"key": "value"})
        result = await cache.get("test-key")
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_missing_key_returns_none(self, mock_redis):
        from memory.redis_memory import MemoryCache
        cache = MemoryCache(mock_redis)
        mock_redis.get.return_value = None
        result = await cache.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get_conversation_history(self, mock_redis):
        from memory.redis_memory import MemoryCache
        import json
        cache = MemoryCache(mock_redis)

        entry = {"role": "user", "content": "hello"}
        mock_redis.lrange.return_value = [json.dumps(entry)]

        await cache.save_message("conv-1", "user", "hello")
        history = await cache.get_conversation_history("conv-1")

        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "hello"

    @pytest.mark.asyncio
    async def test_clear_conversation(self, mock_redis):
        from memory.redis_memory import MemoryCache
        cache = MemoryCache(mock_redis)
        await cache.clear_conversation("conv-1")
        mock_redis.delete.assert_called_once()


# ─────────────────────────── Coding Agent ────────────────────────────

class TestCodingAgent:
    def test_extract_code_blocks_python(self):
        from agents.coding import CodingAgent
        text = "Here is some code:\n```python\ndef hello():\n    print('hi')\n```\nDone."
        snippets = CodingAgent._extract_code_blocks(text)
        assert len(snippets) == 1
        assert snippets[0]["language"] == "python"
        assert "def hello" in snippets[0]["code"]

    def test_extract_code_blocks_multiple(self):
        from agents.coding import CodingAgent
        text = "```python\nx = 1\n```\nAnd:\n```typescript\nconst y = 2;\n```"
        snippets = CodingAgent._extract_code_blocks(text)
        assert len(snippets) == 2
        langs = {s["language"] for s in snippets}
        assert "python" in langs
        assert "typescript" in langs

    def test_extract_code_blocks_no_code(self):
        from agents.coding import CodingAgent
        snippets = CodingAgent._extract_code_blocks("Just plain text, no code blocks.")
        assert snippets == []

    @pytest.mark.asyncio
    async def test_generate_returns_snippets(self):
        from agents.coding import CodingAgent
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="Here:\n```python\ndef add(a, b):\n    return a + b\n```"
        ))
        agent = CodingAgent(mock_llm)
        snippets = await agent.generate("write an add function", "", [])
        assert len(snippets) >= 1
        assert snippets[0]["language"] == "python"


# ─────────────────────────── Memory Agent ────────────────────────────

class TestMemoryAgent:
    @pytest.mark.asyncio
    async def test_get_relevant_history_returns_last_n(self):
        from agents.memory import MemoryAgent
        mock_cache = AsyncMock()
        mock_cache.get_conversation_history = AsyncMock(return_value=[
            {"role": "user", "content": f"msg{i}"} for i in range(20)
        ])
        agent = MemoryAgent(mock_cache)
        history = await agent.get_relevant_history("conv-1", "query", max_messages=6)
        assert len(history) <= 6

    @pytest.mark.asyncio
    async def test_get_relevant_history_handles_error(self):
        from agents.memory import MemoryAgent
        mock_cache = AsyncMock()
        mock_cache.get_conversation_history = AsyncMock(side_effect=Exception("Redis down"))
        agent = MemoryAgent(mock_cache)
        history = await agent.get_relevant_history("conv-1", "query")
        assert history == []

    @pytest.mark.asyncio
    async def test_save_exchange_calls_cache(self):
        from agents.memory import MemoryAgent
        mock_cache = AsyncMock()
        mock_cache.save_message = AsyncMock()
        agent = MemoryAgent(mock_cache)
        await agent.save_exchange("conv-1", "user message", "assistant reply")
        assert mock_cache.save_message.call_count == 2

    @pytest.mark.asyncio
    async def test_save_exchange_handles_error_gracefully(self):
        from agents.memory import MemoryAgent
        mock_cache = AsyncMock()
        mock_cache.save_message = AsyncMock(side_effect=Exception("Redis down"))
        agent = MemoryAgent(mock_cache)
        # Should not raise
        await agent.save_exchange("conv-1", "msg", "reply")
