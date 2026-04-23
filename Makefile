.PHONY: dev test lint format security build docker-up docker-down clean install

# ── Local Development ──────────────────────────────────────────
dev:
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

# ── Dependencies ───────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

# ── Testing ────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov=app --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/ -m unit -v

test-integration:
	pytest tests/ -m integration -v

# ── Code Quality ───────────────────────────────────────────────
lint:
	flake8 src tests app.py --max-line-length=127

format:
	black src tests app.py

format-check:
	black src tests app.py --check

security:
	bandit -r src app.py -ll

# ── Docker ─────────────────────────────────────────────────────
build:
	docker build -t dev-za-ai:latest .

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-restart:
	docker-compose restart api

# ── Agent CLI ──────────────────────────────────────────────────
index:
	python -m src.cli.main index

chat:
	python -m src.cli.main chat

# ── Cleanup ────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

# ── CI (mirrors GitHub Actions) ────────────────────────────────
ci: format-check lint security test
