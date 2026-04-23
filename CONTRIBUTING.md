# Contributing to AI Dev Agent

Thank you for your interest in contributing! Here is everything you need to get started.

---

## Local Setup

```bash
git clone https://github.com/Reaobaka56/dev-za-ai.git
cd dev-za-ai

# Install all dependencies including dev tools
make install-dev

# Copy environment config
cp .env.example .env
# Edit .env — set your LLM_PROVIDER and API key
```

---

## Running the Project

```bash
# API server (hot reload)
make dev

# Full stack (API + Redis + Frontend via Docker)
make docker-up

# Frontend only
make frontend
```

---

## Running Tests

```bash
make test          # All tests
make test-cov      # With HTML coverage report
make test-unit     # Unit tests only (no external services needed)
```

---

## Code Quality

Before submitting a PR, run:

```bash
make ci            # Runs format-check + lint + security + tests
```

Or individually:
```bash
make format        # Auto-format with black
make lint          # Flake8 linting
make security      # Bandit security scan
```

---

## Branch & PR Conventions

- Branch off `main`: `git checkout -b feat/my-feature`
- Keep PRs focused — one feature or fix per PR
- All tests must pass before merge
- Describe **what** and **why** in your PR description

---

## LLM Provider

Set `LLM_PROVIDER` in your `.env`:

| Value | Requires |
|-------|----------|
| `openai` | `OPENAI_API_KEY` |
| `claude` | `ANTHROPIC_API_KEY` |
| `ollama` | Ollama running locally |

For offline development, use `LLM_PROVIDER=ollama` with `ollama pull llama3`.

---

## Project Structure

See the [README Architecture section](README.md#project-architecture) for a full diagram.

Key files to know:
- `src/agent/llm.py` — LLM provider clients
- `src/agent/core.py` — Agent orchestration loop
- `src/agent/vectordb.py` — ChromaDB vector store
- `app.py` — FastAPI entry point
