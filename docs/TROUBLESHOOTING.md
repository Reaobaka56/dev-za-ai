# Troubleshooting Guide

## API won't start

**Symptom:** `uvicorn app:app` fails immediately

**Check:**
```bash
pip install -r requirements.txt   # Missing packages?
cat .env                           # API key / LLM provider set?
python -c "import fastapi"         # Basic import test
```

---

## Redis not connecting

**Symptom:** `Warning: Redis unavailable — caching disabled`

**Fix:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis via Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or via Docker Compose
docker-compose up redis -d
```

---

## LLM provider errors

### Claude: `ANTHROPIC_API_KEY not set`
```bash
# In .env
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=claude
```

### Ollama: `Connection refused`
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama3

# Verify
curl http://localhost:11434/api/tags
```

### OpenAI: `Authentication failed`
```bash
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
```

---

## ChromaDB errors

**Symptom:** `Could not initialize ChromaDB`

**Fix:**
```bash
# Check write permissions
ls -la chroma_db/

# Delete and recreate
rm -rf chroma_db/
python -m src.cli.main index
```

---

## Tests failing

```bash
# Run with verbose output
pytest tests/ -v --tb=long

# Check missing env vars (use MockLLMClient for tests)
export LLM_PROVIDER=mock
pytest tests/ -m unit
```

---

## Docker build slow / bloated

Ensure `.dockerignore` exists and includes `node_modules` and `__pycache__`.

```bash
docker build --no-cache -t dev-za-ai .
docker image ls dev-za-ai
```
