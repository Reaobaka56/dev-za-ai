"""FastAPI backend server for the AI Dev Agent."""
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ..agent.core import AgentOrchestrator, AgentMode
from ..agent.llm import LLMClient
from ..agent.memory import AgentMemory


# Global agent instance
agent: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent
    llm = LLMClient()
    memory = AgentMemory(llm_client=llm)
    agent = AgentOrchestrator(
        root_dir=os.getenv("AGENT_ROOT_DIR", "."),
        llm_client=llm,
        memory=memory
    )
    print("🚀 Agent initialized")
    yield
    print("👋 Agent shutting down")


app = FastAPI(
    title="AI Dev Agent API",
    description="Backend API for the AI Dev Agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": " AI Dev Agent API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "agent_ready": agent is not None}


@app.get("/memory/stats")
async def memory_stats():
    if not agent:
        return {"error": "Agent not initialized"}
    return agent.get_memory_stats()


@app.post("/memory/index")
async def index_project(directory: str = "."):
    if not agent:
        return {"error": "Agent not initialized"}
    result = await agent.index_project(directory)
    return result


@app.get("/memory/search")
async def search_memory(query: str, n: int = 5):
    if not agent:
        return {"error": "Agent not initialized"}
    results = await agent.search_memory(query, n)
    return {"results": results}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive command from client
            data = await websocket.receive_json()

            mode_str = data.get("mode", "chat")
            target = data.get("target")
            description = data.get("description", "")

            try:
                mode = AgentMode(mode_str)
            except ValueError:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid mode: {mode_str}"
                })
                continue

            # Stream agent response
            async for chunk in agent.run(mode, target, description):
                await websocket.send_json({
                    "type": "stream",
                    "content": chunk
                })

            await websocket.send_json({
                "type": "done"
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
