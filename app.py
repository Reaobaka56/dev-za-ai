from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
import logging
import redis
import json
import hashlib

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Dev Agent API",
    description="Context-aware coding agent powered by Claude / GPT-4 / Ollama",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Auth ───────────────────────────────────────────────────────
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "dev-secret-key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


# ── Prometheus Metrics ─────────────────────────────────────────
prediction_counter = Counter("predictions_total", "Total predictions served")
prediction_latency = Histogram("prediction_latency_seconds", "Prediction latency in seconds")
model_error_counter = Counter("model_errors_total", "Total model errors")


# ── Request / Response Schemas ─────────────────────────────────
class PredictRequest(BaseModel):
    input: dict = Field(..., description="Input data for the model")
    model_version: str = Field(default="latest", description="Model version to use")


class PredictResponse(BaseModel):
    prediction: dict
    latency_ms: float
    cached: bool
    model_version: str


# ── Model ──────────────────────────────────────────────────────
class DummyModel:
    def predict(self, data: dict) -> dict:
        return {"result": "success", "input_keys": list(data.keys())}


def load_model():
    return DummyModel()


model = load_model()

# ── Redis Cache ────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    logger.warning(f"Redis unavailable — caching disabled: {e}")
    redis_client = None


# ── Lifecycle ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info(f"AI Dev Agent API started | provider={os.getenv('LLM_PROVIDER', 'openai')}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Graceful shutdown — closing connections...")
    if redis_client:
        redis_client.close()


# ── Health ─────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    """Liveness probe — always returns 200 if process is alive."""
    return {"status": "alive"}


@app.get("/ready", tags=["Health"])
async def readiness():
    """Readiness probe — checks model + Redis availability."""
    checks = {"model": False, "redis": False}
    try:
        model.predict({"test": True})
        checks["model"] = True
    except Exception as e:
        logger.error(f"Model check failed: {e}")

    if redis_client:
        try:
            redis_client.ping()
            checks["redis"] = True
        except Exception:
            pass
    else:
        checks["redis"] = "disabled"

    all_ok = checks["model"] is True
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


# ── Predict ────────────────────────────────────────────────────
@app.post("/predict", response_model=PredictResponse, tags=["Inference"])
@limiter.limit("10/minute")
async def predict(
    request: Request,
    body: PredictRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Run model inference.

    - Requires `X-API-Key` header
    - Rate limited to 10 requests/minute per IP
    - Responses cached in Redis for 1 hour
    """
    start = time.time()
    try:
        # Cache lookup
        cache_key = None
        if redis_client:
            raw = json.dumps(body.input, sort_keys=True) + body.model_version
            cache_key = f"pred:{hashlib.md5(raw.encode()).hexdigest()}"
            cached = redis_client.get(cache_key)
            if cached:
                prediction_counter.inc()
                prediction_latency.observe(time.time() - start)
                return PredictResponse(
                    prediction=json.loads(cached),
                    latency_ms=(time.time() - start) * 1000,
                    cached=True,
                    model_version=body.model_version,
                )

        # Inference
        result = model.predict(body.input)

        # Cache result
        if redis_client and cache_key:
            redis_client.setex(cache_key, 3600, json.dumps(result))

        prediction_counter.inc()
        prediction_latency.observe(time.time() - start)
        return PredictResponse(
            prediction=result,
            latency_ms=(time.time() - start) * 1000,
            cached=False,
            model_version=body.model_version,
        )

    except Exception as e:
        model_error_counter.inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Metrics ────────────────────────────────────────────────────
@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics endpoint for Grafana scraping."""
    return PlainTextResponse(generate_latest())
