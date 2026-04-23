# API Reference

Base URL: `http://localhost:8000`

All endpoints except `/health` and `/ready` require the header:
```
X-API-Key: <your-api-key>
```

---

## Endpoints

### `GET /health`
Liveness probe. Always returns 200 if the process is running.

```json
{ "status": "alive" }
```

---

### `GET /ready`
Readiness probe. Checks model + Redis.

```json
{
  "status": "ready",
  "checks": { "model": true, "redis": true }
}
```

---

### `POST /predict`
Run model inference.

**Rate limit:** 10 requests/minute per IP

**Request:**
```json
{
  "input": { "code": "def foo(): return user.name", "action": "fix" },
  "model_version": "latest"
}
```

**Response:**
```json
{
  "prediction": { "result": "success", "input_keys": ["code", "action"] },
  "latency_ms": 12.4,
  "cached": false,
  "model_version": "latest"
}
```

---

### `GET /metrics`
Prometheus metrics for Grafana scraping.

---

### `GET /docs`
Interactive Swagger UI.

### `GET /redoc`
ReDoc API documentation.

---

## `src/api/v1` Routes

### `POST /api/v1/explain`
```json
{ "file_path": "src/agent/core.py" }
```

### `POST /api/v1/search`
```json
{ "query": "function that loads model", "directory": "." }
```

### `GET /api/v1/files?directory=src&pattern=*.py`
List files matching a pattern.
