from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
import time
import logging

app = FastAPI()

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
async def predict(data: dict):
    """Main prediction endpoint with metrics"""
    start = time.time()
    try:
        result = model.predict(data)
        prediction_counter.inc()
        prediction_latency.observe(time.time() - start)
        return {"prediction": result, "latency_ms": (time.time() - start) * 1000}
    except Exception as e:
        model_error_counter.inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())
