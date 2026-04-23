"""Vector memory layer using ChromaDB for long-term project memory."""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None

from .code_parser import CodeParser, CodeChunk
from .llm import LLMClient


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class AgentMemory:
    """Vector-based memory for the agent."""

    def __init__(self, 
                 collection_name: str = "codebase",
                 persist_dir: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None):
        self.collection_name = collection_name
        self.persist_dir = persist_dir or os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.llm = llm_client or LLMClient()
        self.parser = CodeParser()
        self.collection = None
        self._init_db()

    def _init_db(self):
        """Initialize ChromaDB connection."""
        if not CHROMA_AVAILABLE:
            print("Warning: ChromaDB not available. Running in memory-only mode.")
            return

        try:
            client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Warning: Could not initialize ChromaDB: {e}")

    def _generate_id(self, content: str, file_path: str, start_line: int) -> str:
        """Generate a unique ID for a chunk."""
        key = f"{file_path}:{start_line}:{content[:100]}"
        return hashlib.md5(key.encode()).hexdigest()

    async def index_file(self, file_path: str) -> int:
        """Index a single file into vector memory."""
        if not self.collection:
            return 0

        chunks = self.parser.parse_file(file_path)
        if not chunks:
            return 0

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.llm.embed(texts)

        # Prepare batch
        ids = []
        documents = []
        metadatas = []
        embeds = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = self._generate_id(chunk.content, chunk.file_path, chunk.start_line)
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append({
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name or "",
                "language": chunk.language
            })
            embeds.append(embedding)

        # Upsert to collection
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeds
        )

        return len(chunks)

    async def index_project(self, root_dir: str = ".", 
                          extensions: Optional[List[str]] = None) -> Dict[str, int]:
        """Index an entire project directory."""
        if not self.collection:
            return {"indexed": 0, "errors": 0}

        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"]

        root = Path(root_dir).resolve()
        files = []

        for ext in extensions:
            files.extend(root.rglob(f"*{ext}"))

        # Filter out common non-source directories
        skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".pytest_cache", "dist", "build"}
        files = [
            f for f in files 
            if not any(part in skip_dirs for part in f.parts)
        ]

        indexed = 0
        errors = 0

        for file_path in files:
            try:
                count = await self.index_file(str(file_path))
                indexed += count
            except Exception as e:
                errors += 1
                print(f"Error indexing {file_path}: {e}")

        return {"indexed": indexed, "errors": errors, "files": len(files)}

    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search memory for relevant code chunks."""
        if not self.collection:
            return []

        query_embedding = await self.llm.embed([query])

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.collection:
            return {"status": "unavailable", "count": 0}

        return {
            "status": "active",
            "count": self.collection.count(),
            "collection": self.collection_name,
            "persist_dir": self.persist_dir
        }

    def clear(self):
        """Clear all memories."""
        if self.collection:
            ids = self.collection.get()["ids"]
            if ids:
                self.collection.delete(ids=ids)


class SimpleMemory:
    """Fallback in-memory storage when ChromaDB is unavailable."""

    def __init__(self):
        self.entries: List[MemoryEntry] = []

    async def index_file(self, file_path: str) -> int:
        return 0

    async def index_project(self, root_dir: str = ".", extensions=None):
        return {"indexed": 0, "errors": 0}

    async def search(self, query: str, n_results: int = 5):
        return []

    def get_stats(self):
        return {"status": "simple_memory", "count": len(self.entries)}
