"""LLM integration layer supporting Claude (Anthropic), Ollama (local), and OpenAI."""
import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

load_dotenv()


# ──────────────────────────────────────────────────────────────
# Shared message dataclass
# ──────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Claude (Anthropic) Client
# ──────────────────────────────────────────────────────────────

class ClaudeLLMClient:
    """LLM client backed by Anthropic Claude (claude-3-5-sonnet, claude-3-opus, etc.)."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment.")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
        stream: bool = False,
    ) -> Message:
        """Send a request to the Claude Messages API."""
        import asyncio

        system_prompt = ""
        formatted = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "max_tokens": 8192,
            "temperature": temperature,
            "messages": formatted,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        # Run blocking call in executor to stay async-compatible
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.client.messages.create(**kwargs)
        )

        content = response.content[0].text if response.content else ""
        return Message(role="assistant", content=content)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Claude doesn't natively embed — fall back to a mock or raise."""
        raise NotImplementedError(
            "Claude does not provide an embedding API. "
            "Set LLM_PROVIDER=openai for embeddings, or use Ollama embeddings."
        )

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """Stream Claude response token by token."""
        import asyncio

        system_prompt = ""
        formatted = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "max_tokens": 8192,
            "temperature": temperature,
            "messages": formatted,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


# ──────────────────────────────────────────────────────────────
# Ollama (Local) Client
# ──────────────────────────────────────────────────────────────

class OllamaLLMClient:
    """LLM client backed by a locally-running Ollama server.

    Supports any model pulled via `ollama pull <model>`.
    Great for offline usage, fine-tuning, and data privacy.
    """

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
        stream: bool = False,
    ) -> Message:
        """Send a request to the local Ollama /api/chat endpoint."""
        import httpx

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat", json=payload
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return Message(role="assistant", content=content)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Use Ollama's /api/embeddings endpoint (requires embedding-capable model)."""
        import httpx

        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
        return embeddings

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama."""
        import httpx

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            pass


# ──────────────────────────────────────────────────────────────
# OpenAI Client (original, unchanged)
# ──────────────────────────────────────────────────────────────

class LLMClient:
    """Unified LLM client supporting OpenAI and local models."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if AsyncOpenAI and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
        stream: bool = False
    ) -> Message:
        """Send chat completion request."""
        if not self.client:
            raise RuntimeError("LLM client not initialized. Check API key.")

        formatted_msgs = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            formatted_msgs.append(m)

        kwargs = {
            "model": self.model,
            "messages": formatted_msgs,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        msg = choice.message

        return Message(
            role=msg.role,
            content=msg.content or "",
            tool_calls=[tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        if not self.client:
            raise RuntimeError("LLM client not initialized.")

        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = await self.client.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Stream chat response token by token."""
        if not self.client:
            yield "Error: LLM client not initialized."
            return

        formatted_msgs = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        kwargs = {
            "model": self.model,
            "messages": formatted_msgs,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        stream_response = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream_response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ──────────────────────────────────────────────────────────────
# Factory — auto-select provider from LLM_PROVIDER env var
# ──────────────────────────────────────────────────────────────

def create_llm_client(provider: Optional[str] = None) -> "LLMClient | ClaudeLLMClient | OllamaLLMClient":
    """
    Factory that returns the correct LLM client based on LLM_PROVIDER env var.

    Set in your .env:
        LLM_PROVIDER=claude    → Uses Anthropic Claude (requires ANTHROPIC_API_KEY)
        LLM_PROVIDER=ollama    → Uses local Ollama server (requires OLLAMA_MODEL)
        LLM_PROVIDER=openai    → Uses OpenAI (requires OPENAI_API_KEY) [default]
    """
    provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "claude":
        return ClaudeLLMClient()
    elif provider == "ollama":
        return OllamaLLMClient()
    else:
        return LLMClient()


# ──────────────────────────────────────────────────────────────
# Mock client for tests
# ──────────────────────────────────────────────────────────────

class MockLLMClient:
    """Mock LLM for testing without API keys."""

    async def chat(self, messages, tools=None, temperature=0.1, stream=False):
        last_msg = messages[-1].content if messages else ""
        return Message(
            role="assistant",
            content=f"[Mock] I would process: {last_msg[:100]}..."
        )

    async def embed(self, texts):
        return [[0.1] * 1536 for _ in texts]

    async def stream_chat(self, messages, tools=None, temperature=0.1):
        yield "[Mock] Streaming response..."



@dataclass
class Message:
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class LLMClient:
    """Unified LLM client supporting OpenAI and local models."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if AsyncOpenAI and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1,
        stream: bool = False
    ) -> Message:
        """Send chat completion request."""
        if not self.client:
            raise RuntimeError("LLM client not initialized. Check API key.")

        formatted_msgs = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            formatted_msgs.append(m)

        kwargs = {
            "model": self.model,
            "messages": formatted_msgs,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        msg = choice.message

        return Message(
            role=msg.role,
            content=msg.content or "",
            tool_calls=[tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        if not self.client:
            raise RuntimeError("LLM client not initialized.")

        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = await self.client.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Stream chat response token by token."""
        if not self.client:
            yield "Error: LLM client not initialized."
            return

        formatted_msgs = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        kwargs = {
            "model": self.model,
            "messages": formatted_msgs,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        stream_response = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream_response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockLLMClient:
    """Mock LLM for testing without API keys."""

    async def chat(self, messages, tools=None, temperature=0.1, stream=False):
        last_msg = messages[-1].content if messages else ""
        return Message(
            role="assistant",
            content=f"[Mock] I would process: {last_msg[:100]}..."
        )

    async def embed(self, texts):
        return [[0.1] * 1536 for _ in texts]

    async def stream_chat(self, messages, tools=None, temperature=0.1):
        yield "[Mock] Streaming response..."
