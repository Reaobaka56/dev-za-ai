from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
import logging
import redis
import json
import hashlib

app = FastAPI()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authentication
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "dev-secret-key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key
# Metrics
prediction_counter = Counter('predictions_total', 'Total predictions')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')
model_error_counter = Counter('model_errors_total', 'Model errors')

logger = logging.getLogger(__name__)

# Dummy model for demonstration
class DummyModel:
    def predict(self, data):
        return {"result": "success", "input": data}

def load_model():
    return DummyModel()

# Load model once at startup
model = load_model()

# Redis Caching Layer
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL)
    # Test connection
    redis_client.ping()
except Exception as e:
    logger.warning(f"Could not connect to Redis, caching disabled: {e}")
    redis_client = None

@app.on_event("startup")
async def startup():
    logger.info("Model loaded successfully")

@app.get("/health")
async def health():
    """Liveness probe"""
    return {"status": "alive"}

@app.get("/ready")
async def readiness():
    """Readiness probe"""
    try:
        # Test model inference
        model.predict({"test": True})
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "not ready"})

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, data: dict, api_key: str = Depends(get_api_key)):
    """Main prediction endpoint with metrics, rate limiting, and auth"""
    start = time.time()
    try:
        # Check cache
        cache_key = None
        if redis_client:
            cache_key = f"pred:{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()}"
            cached_result = redis_client.get(cache_key)
            if cached_result:
                prediction_counter.inc()
                prediction_latency.observe(time.time() - start)
                return {
                    "prediction": json.loads(cached_result), 
                    "latency_ms": (time.time() - start) * 1000,
                    "cached": True
                }

        # Compute prediction
        result = model.predict(data)
        
        # Save to cache
        if redis_client and cache_key:
            redis_client.setex(cache_key, 3600, json.dumps(result)) # 1 hr TTL

        prediction_counter.inc()
        prediction_latency.observe(time.time() - start)
        return {"prediction": result, "latency_ms": (time.time() - start) * 1000, "cached": False}
    except Exception as e:
        model_error_counter.inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())
