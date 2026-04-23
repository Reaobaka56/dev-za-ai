#  AI Dev Agent

An intelligent coding agent that understands your codebase, fixes bugs, refactors code, and explains architecture.

## Features

- **Code Understanding**: AST parsing for Python, JS, TS
- **Vector Memory**: Long-term project memory via ChromaDB
- **Agent Loop**: Reasoning + tool use with feedback
- **CLI Interface**: Commands like `agent fix bug`, `agent explain file`
- **FastAPI Backend**: Real-time WebSocket updates
- **Git Integration**: Automatic commits and branch creation

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Run the agent
# CLI mode:
python -m src.cli.main fix auth.py --description "login bug"

# Server mode:
python -m src.api.server
```

## Architecture

```
CLI/VS Code → FastAPI → Agent Orchestrator → LLM + Tools + Memory
                                    ↓
                              Codebase + Git
```

## Commands

| Command | Description |
|---------|-------------|
| `explain <file>` | Explain what a file does |
| `fix <file>` | Fix bugs in a file |
| `refactor <file>` | Refactor for better quality |
| `ask "<question>"` | Ask about the codebase |
| `index` | Index the current project |
| `chat` | Interactive chat mode |

## Tech Stack

- **LLM**: OpenAI GPT-4o / GPT-4.1
- **Embeddings**: text-embedding-3-small
- **Vector DB**: ChromaDB
- **AST Parsing**: tree-sitter
- **API**: FastAPI + WebSocket
- **CLI**: Typer + Rich
