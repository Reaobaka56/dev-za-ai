# AI Dev Agent

> An intelligent coding agent that understands your entire codebase, fixes bugs, refactors code, and explains architecture — powered by **Claude**, **OpenAI GPT-4**, or a **local Ollama model**.

---

## Table of Contents

1. [Features](#features)
2. [Project Architecture](#project-architecture)
3. [LLM Providers](#llm-providers)
4. [VectorDB & Memory](#vectordb--memory)
5. [Quick Start](#quick-start)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [CLI Commands](#cli-commands)
9. [Tech Stack](#tech-stack)
10. [Docker & Kubernetes](#docker--kubernetes)

---

## Features

| Feature | Description |
|---------|-------------|
| 🧠 **Context-Aware Fixes** | AST parsing for Python, JS, TS gives the agent deep code understanding |
| 🔍 **Vector Memory** | ChromaDB-backed semantic search across your entire codebase |
| 🤖 **Multi-Provider LLM** | Claude, OpenAI GPT-4, or Ollama (local) — switchable via one env var |
| ⚡ **Sub-second Caching** | Redis caches repeat predictions for 1-hour TTL |
| 🔐 **Secure API** | API-key auth + rate limiting on all endpoints |
| 📡 **Real-time Streaming** | WebSocket + SSE token streaming for live output |
| 🛠️ **CLI Interface** | Rich terminal UI: `agent fix`, `agent explain`, `agent chat` |
| 📊 **Prometheus Metrics** | `/metrics` endpoint ready for Grafana dashboards |
| 🚀 **Kubernetes Ready** | HPA autoscaling, liveness/readiness probes, Docker support |
| 🔄 **CI/CD Pipeline** | GitHub Actions: test → security scan → Docker build |

---

## Project Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                  │
│   CLI (Typer)   │   FastAPI REST   │   WebSocket (real-time)     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                       API GATEWAY (FastAPI)                      │
│  Auth (API Key)  │  Rate Limiting (slowapi)  │  /metrics         │
│  /predict  │  /health  │  /ready  │  /ws/<session>              │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    AGENT ORCHESTRATOR (core.py)                  │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │  LLM Client    │  │  Tool Runner   │  │  Memory / Search │   │
│  │  (llm.py)      │  │  (tools.py)    │  │  (memory.py)     │   │
│  └───────┬────────┘  └───────┬────────┘  └────────┬─────────┘   │
│          │                   │                     │             │
└──────────┼───────────────────┼─────────────────────┼────────────┘
           │                   │                     │
     ┌─────▼─────┐      ┌──────▼──────┐      ┌──────▼──────────┐
     │ LLM Layer │      │ Tool Layer  │      │  VectorDB Layer  │
     │           │      │             │      │  (vectordb.py)   │
     │ ┌───────┐ │      │ read_file   │      │                  │
     │ │Claude │ │      │ write_file  │      │  ┌────────────┐  │
     │ │OpenAI │ │      │ run_tests   │      │  │ ChromaDB   │  │
     │ │Ollama │ │      │ git_commit  │      │  │ Persistent │  │
     │ └───────┘ │      │ web_search  │      │  └────────────┘  │
     └───────────┘      └─────────────┘      └──────────────────┘
           │                                          │
     ┌─────▼──────────────────────────────────────────▼──────────┐
     │                    INFRASTRUCTURE                          │
     │   Redis (cache)  │  PostgreSQL (future)  │  Git (history) │
     └────────────────────────────────────────────────────────────┘
```

### Directory Layout

```
dev-za-ai/
├── app.py                          # FastAPI entry point (predict, health, metrics)
├── Dockerfile                      # Container build definition
├── k8s-deployment.yaml             # Kubernetes Deployment + HPA
├── requirements.txt                # Python dependencies
├── .env.example                    # All supported config keys
├── ENTERPRISE_READINESS.md         # Gap analysis & action plan
│
├── src/
│   ├── agent/
│   │   ├── core.py                 # Agent orchestration loop
│   │   ├── llm.py                  # Claude / OpenAI / Ollama clients + factory
│   │   ├── vectordb.py             # VectorDB abstraction (ChromaDB)
│   │   ├── memory.py               # Project indexing + semantic search
│   │   ├── code_parser.py          # AST parsing (Python, JS, TS)
│   │   └── tools.py                # Tool implementations (read, write, git…)
│   ├── api/
│   │   ├── server.py               # FastAPI app factory
│   │   ├── routes.py               # REST route definitions
│   │   └── websocket.py            # WebSocket streaming handler
│   └── cli/
│       └── main.py                 # Typer CLI (fix, explain, chat, index…)
│
├── tests/
│   ├── test_agent.py
│   └── test_tools.py
│
├── frontend/                       # React landing page (Vite)
│   └── src/
│       ├── App.jsx                 # Landing page with demo, diff, testimonials
│       └── index.css
│
└── .github/
    └── workflows/
        └── ci-cd.yml               # Test → Security scan → Docker build
```

---

## LLM Providers

Switch providers by setting `LLM_PROVIDER` in your `.env` file. No code changes required.

### Option 1 — Claude (Anthropic) ⭐ Recommended

```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022   # or claude-3-opus-20240229
```

Best for: highest coding accuracy, long context windows, tool use.

### Option 2 — OpenAI GPT-4

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini                    # or gpt-4o, gpt-4-turbo
EMBEDDING_MODEL=text-embedding-3-small
```

Best for: embeddings, familiarity, wide ecosystem support.

### Option 3 — Ollama (Local / Offline) 🔒 Privacy-first

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3                       # or mistral, codellama, phi3
```

Requirements: [Install Ollama](https://ollama.ai) and pull a model first:
```bash
ollama pull llama3          # General purpose
ollama pull codellama       # Code-optimised
ollama pull mistral         # Lightweight + fast
```

Best for: local development, air-gapped environments, data privacy.

---

## VectorDB & Memory

The agent indexes your codebase into **ChromaDB** for semantic search.

### How it works

```
Source Files (py, js, ts…)
        ↓
   AST Parsing (code_parser.py)
        ↓
   Text Chunks (functions, classes, methods)
        ↓
   Embeddings (via LLM provider)
        ↓
   ChromaDB (persisted to ./chroma_db)
        ↓
   Semantic Search at query time
```

### Index your project

```bash
# CLI
python -m src.cli.main index

# API
POST /predict  { "action": "index", "path": "." }
```

### Configuration

```bash
CHROMA_DB_PATH=./chroma_db   # Where ChromaDB persists data
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Reaobaka56/dev-za-ai.git
cd dev-za-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your LLM provider
cp .env.example .env
# Edit .env — set LLM_PROVIDER and corresponding API key

# 4a. Run the API server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 4b. Or run the CLI
python -m src.cli.main chat

# 5. (Optional) Run with Docker
docker build -t dev-za-ai .
docker run -p 8000:8000 --env-file .env dev-za-ai
```

---

## Configuration

All configuration is done through environment variables (copy `.env.example` → `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | `openai` \| `claude` \| `ollama` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=claude` |
| `CLAUDE_MODEL` | `claude-3-5-sonnet-20241022` | Claude model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Model to use with Ollama |
| `CHROMA_DB_PATH` | `./chroma_db` | ChromaDB persistence directory |
| `API_KEY` | `dev-secret-key` | API key for `/predict` auth header `X-API-Key` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for prediction caching |

---

## API Reference

All endpoints except `/health` and `/ready` require the `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (tests model) |
| `POST` | `/predict` | Run prediction (rate limited: 10/min) |
| `GET` | `/metrics` | Prometheus metrics |

**Example request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"code": "def foo(): return user.name", "action": "fix"}'
```

---

## CLI Commands

```bash
python -m src.cli.main <command>
```

| Command | Description |
|---------|-------------|
| `fix <file>` | Detect and fix bugs in a file |
| `explain <file>` | Explain what a file does |
| `refactor <file>` | Refactor for readability and performance |
| `ask "<question>"` | Ask a question about the codebase |
| `index` | Index the entire project into VectorDB |
| `chat` | Start an interactive chat session |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Claude 3.5 Sonnet / GPT-4o / Ollama (llama3, codellama) |
| **Embeddings** | text-embedding-3-small (OpenAI) or Ollama embeddings |
| **Vector DB** | ChromaDB (persistent, cosine similarity) |
| **AST Parsing** | tree-sitter (Python, JS, TS) |
| **API** | FastAPI + Uvicorn |
| **Auth** | API Key header + slowapi rate limiting |
| **Cache** | Redis (1-hour TTL) |
| **Monitoring** | Prometheus client + custom metrics |
| **CLI** | Typer + Rich |
| **Frontend** | React + Vite |
| **CI/CD** | GitHub Actions (test, scan, build) |

---

## Docker & Kubernetes

```bash
# Build and run locally
docker build -t dev-za-ai .
docker run -p 8000:8000 --env-file .env dev-za-ai

# Deploy to Kubernetes (3 replicas + HPA)
kubectl apply -f k8s-deployment.yaml
kubectl get pods -l app=ml-model
```

The Kubernetes config includes:
- **3 replicas** minimum, scales to **20** based on CPU/memory
- **Liveness probe** → `/health`
- **Readiness probe** → `/ready`
- **HPA** → triggers at 70% CPU or 80% memory
