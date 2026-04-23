# Deployment Guide

## Local (Development)

```bash
make install-dev
cp .env.example .env
make dev
```

---

## Docker Compose (Recommended for local full-stack)

```bash
cp .env.example .env
# Edit .env with real API keys

docker-compose up --build -d

# Verify all services
docker-compose ps
docker-compose logs -f api
```

Services started:
| Service | Port |
|---------|------|
| API | 8000 |
| Redis | 6379 |
| Frontend | 5173 |

---

## Docker (API only)

```bash
docker build -t dev-za-ai .
docker run -p 8000:8000 --env-file .env dev-za-ai
```

---

## Kubernetes

```bash
# Create secret for API key
kubectl create secret generic agent-secrets \
  --from-literal=API_KEY=your-secret-key \
  --from-literal=OPENAI_API_KEY=sk-...

# Deploy
kubectl apply -f k8s-deployment.yaml

# Check rollout
kubectl rollout status deployment/ml-model-api
kubectl get pods -l app=ml-model
```

The k8s config includes:
- 3 replicas minimum, 20 maximum (HPA)
- Liveness probe: `/health`
- Readiness probe: `/ready`
- Autoscales at 70% CPU / 80% memory

---

## Environment Variables

See `.env.example` for the full list.

Key production variables:
```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
API_KEY=<strong-random-key>
REDIS_URL=redis://<host>:6379/0
CHROMA_DB_PATH=/data/chroma_db
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
```
