"""Expanded test suite covering LLM clients, VectorDB, API endpoints, and caching."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.agent.core import SimpleAgent, AgentOrchestrator, AgentMode
from src.agent.llm import MockLLMClient, Message, OllamaLLMClient, create_llm_client
from src.agent.vectordb import VectorDB
from app import app


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def vector_db():
    """In-memory VectorDB for fast unit tests."""
    return VectorDB(collection="test", in_memory=True)


@pytest.fixture
def mock_llm():
    return MockLLMClient()


# ──────────────────────────────────────────────────────────────
# SimpleAgent tests
# ──────────────────────────────────────────────────────────────

class TestSimpleAgent:
    def test_explain_file(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def add(a, b):\n"
            "    return a + b\n\n"
            "class Calculator:\n"
            "    def multiply(self, a, b):\n"
            "        return a * b\n"
        )
        agent = SimpleAgent(str(tmp_path))
        result = agent.explain_file(str(test_file))

        assert "add" in result
        assert "Calculator" in result
        assert "multiply" in result


# ──────────────────────────────────────────────────────────────
# AgentMode tests
# ──────────────────────────────────────────────────────────────

class TestAgentMode:
    def test_modes(self):
        assert AgentMode.FIX.value == "fix"
        assert AgentMode.EXPLAIN.value == "explain"
        assert AgentMode.REFACTOR.value == "refactor"
        assert AgentMode.ASK.value == "ask"
        assert AgentMode.CHAT.value == "chat"


# ──────────────────────────────────────────────────────────────
# MockLLMClient tests
# ──────────────────────────────────────────────────────────────

class TestMockLLMClient:
    @pytest.mark.asyncio
    async def test_chat_returns_message(self, mock_llm):
        msg = Message(role="user", content="Hello")
        response = await mock_llm.chat([msg])
        assert response.role == "assistant"
        assert "[Mock]" in response.content

    @pytest.mark.asyncio
    async def test_embed_returns_vectors(self, mock_llm):
        embeddings = await mock_llm.embed(["test text", "another text"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536

    @pytest.mark.asyncio
    async def test_stream_chat(self, mock_llm):
        msg = Message(role="user", content="stream test")
        tokens = []
        async for token in mock_llm.stream_chat([msg]):
            tokens.append(token)
        assert len(tokens) > 0


# ──────────────────────────────────────────────────────────────
# LLM Factory tests
# ──────────────────────────────────────────────────────────────

class TestLLMFactory:
    def test_create_openai_client(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        from src.agent.llm import LLMClient
        client = create_llm_client("openai")
        assert isinstance(client, LLMClient)

    def test_create_ollama_client(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        client = create_llm_client("ollama")
        assert isinstance(client, OllamaLLMClient)
        assert client.model is not None


# ──────────────────────────────────────────────────────────────
# VectorDB tests
# ──────────────────────────────────────────────────────────────

class TestVectorDB:
    @pytest.mark.asyncio
    async def test_upsert_and_stats(self, vector_db):
        ok = await vector_db.upsert(
            doc_id="test-1",
            content="def hello(): return 'world'",
            metadata={"file": "main.py"},
        )
        assert ok is True
        stats = vector_db.stats()
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_upsert_batch(self, vector_db):
        items = [
            {"id": f"item-{i}", "content": f"code chunk {i}", "metadata": {"idx": i}}
            for i in range(5)
        ]
        count = await vector_db.upsert_batch(items)
        assert count == 5

    @pytest.mark.asyncio
    async def test_delete(self, vector_db):
        await vector_db.upsert("del-1", "some code", {})
        deleted = await vector_db.delete("del-1")
        assert deleted is True

    @pytest.mark.asyncio
    async def test_clear(self, vector_db):
        await vector_db.upsert("a", "code a", {})
        await vector_db.upsert("b", "code b", {})
        count = await vector_db.clear()
        assert count == 2
        assert vector_db.stats()["count"] == 0

    def test_make_id_deterministic(self):
        id1 = VectorDB.make_id("same content", "ns")
        id2 = VectorDB.make_id("same content", "ns")
        assert id1 == id2

    def test_make_id_unique(self):
        id1 = VectorDB.make_id("content a")
        id2 = VectorDB.make_id("content b")
        assert id1 != id2


# ──────────────────────────────────────────────────────────────
# FastAPI endpoint tests
# ──────────────────────────────────────────────────────────────

class TestAPIEndpoints:
    def test_health(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_ready(self, api_client):
        response = api_client.get("/ready")
        # Model should respond (redis may be unavailable in test env)
        assert response.status_code in (200, 503)
        assert "status" in response.json()

    def test_predict_no_auth(self, api_client):
        response = api_client.post("/predict", json={"input": {"key": "value"}})
        assert response.status_code == 403

    def test_predict_with_auth(self, api_client, monkeypatch):
        monkeypatch.setenv("API_KEY", "test-key")
        import importlib
        import app as app_module
        importlib.reload(app_module)

        client = TestClient(app_module.app)
        response = client.post(
            "/predict",
            json={"input": {"key": "value"}, "model_version": "latest"},
            headers={"X-API-Key": "test-key"},
        )
        # 200 OK or 429 if rate limited
        assert response.status_code in (200, 429)

    def test_metrics_endpoint(self, api_client):
        response = api_client.get("/metrics")
        assert response.status_code == 200
        assert b"predictions_total" in response.content
