"""LLM integration layer with OpenAI and local model support."""
import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

load_dotenv()


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
