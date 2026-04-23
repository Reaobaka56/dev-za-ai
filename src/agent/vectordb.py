"""
VectorDB abstraction layer — wraps ChromaDB with a clean API.

Supports:
  - Persistent local ChromaDB (default)
  - In-memory ChromaDB (for tests)
  - Future: Qdrant, Pinecone, Weaviate (via adapters)

Usage:
    from src.agent.vectordb import VectorDB

    db = VectorDB(collection="my_project")
    await db.upsert("doc-1", "def my_func(): pass", {"file": "main.py"})
    results = await db.search("function that does X", n=5)
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None


@dataclass
class SearchResult:
    """A single vector search match."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float  # lower = closer in cosine distance


class VectorDB:
    """
    High-level VectorDB interface backed by ChromaDB.

    Initializes a persistent ChromaDB collection at CHROMA_DB_PATH
    (defaults to ./chroma_db). Falls back to a no-op if ChromaDB
    is not installed.
    """

    def __init__(
        self,
        collection: str = "codebase",
        persist_dir: Optional[str] = None,
        in_memory: bool = False,
    ):
        self.collection_name = collection
        self.persist_dir = persist_dir or os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.in_memory = in_memory
        self._collection = None
        self._init()

    # ──────────────────────────────────────────
    # Init
    # ──────────────────────────────────────────

    def _init(self):
        if not CHROMA_AVAILABLE:
            print("⚠️  ChromaDB not installed — VectorDB running in no-op mode.")
            return

        try:
            if self.in_memory:
                client = chromadb.EphemeralClient()
            else:
                client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"⚠️  VectorDB init failed: {e}")

    # ──────────────────────────────────────────
    # Write
    # ──────────────────────────────────────────

    async def upsert(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> bool:
        """Insert or update a single document in the vector store."""
        if not self._collection:
            return False

        kwargs: Dict[str, Any] = {
            "ids": [doc_id],
            "documents": [content],
            "metadatas": [metadata or {}],
        }
        if embedding:
            kwargs["embeddings"] = [embedding]

        self._collection.upsert(**kwargs)
        return True

    async def upsert_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> int:
        """
        Batch upsert a list of items.

        Each item must contain:
            - id: str
            - content: str
            - metadata: dict (optional)
            - embedding: list[float] (optional)
        """
        if not self._collection:
            return 0

        ids = [i["id"] for i in items]
        docs = [i["content"] for i in items]
        metas = [i.get("metadata", {}) for i in items]
        embeds = [i["embedding"] for i in items if "embedding" in i]

        kwargs: Dict[str, Any] = {
            "ids": ids,
            "documents": docs,
            "metadatas": metas,
        }
        if embeds and len(embeds) == len(ids):
            kwargs["embeddings"] = embeds

        self._collection.upsert(**kwargs)
        return len(ids)

    # ──────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────

    async def search(
        self,
        query_embedding: List[float],
        n: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search the collection using a pre-computed embedding vector.
        Use `search_text()` if you want to pass a raw string query.
        """
        if not self._collection:
            return []

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(n, self._collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self._collection.query(**kwargs)

        results = []
        for i in range(len(raw["ids"][0])):
            results.append(SearchResult(
                id=raw["ids"][0][i],
                content=raw["documents"][0][i],
                metadata=raw["metadatas"][0][i],
                score=raw["distances"][0][i],
            ))
        return results

    async def get(self, doc_id: str) -> Optional[SearchResult]:
        """Fetch a single document by ID."""
        if not self._collection:
            return None

        raw = self._collection.get(ids=[doc_id], include=["documents", "metadatas"])
        if not raw["ids"]:
            return None

        return SearchResult(
            id=raw["ids"][0],
            content=raw["documents"][0],
            metadata=raw["metadatas"][0],
            score=0.0,
        )

    # ──────────────────────────────────────────
    # Delete / Reset
    # ──────────────────────────────────────────

    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if not self._collection:
            return False
        self._collection.delete(ids=[doc_id])
        return True

    async def clear(self) -> int:
        """Delete all documents from this collection. Returns count deleted."""
        if not self._collection:
            return 0
        ids = self._collection.get()["ids"]
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    # ──────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        if not self._collection:
            return {"status": "unavailable", "count": 0, "backend": "none"}

        return {
            "status": "active",
            "backend": "chromadb",
            "collection": self.collection_name,
            "count": self._collection.count(),
            "persist_dir": None if self.in_memory else self.persist_dir,
        }

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    @staticmethod
    def make_id(content: str, namespace: str = "") -> str:
        """Generate a stable, deterministic ID from content."""
        key = f"{namespace}:{content[:200]}"
        return hashlib.md5(key.encode()).hexdigest()
