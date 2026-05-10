# Multi-Agent AI Research Assistant — Makefile
# Usage: make <target>

.PHONY: help setup dev up down logs test lint format migrate seed clean

# ── Colors ───────────────────────────────────────────────────────────────────
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

help: ## Show this help
	@echo ""
	@echo "$(CYAN)Multi-Agent AI Research Assistant$(RESET)"
	@echo "────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Setup ────────────────────────────────────────────────────────────────────
setup: ## First-time setup: copy env, install deps
	@echo "$(CYAN)Setting up environment...$(RESET)"
	@[ -f .env ] || cp .env.example .env && echo "  Created .env from .env.example"
	@[ -f frontend/.env.local ] || cp frontend/.env.local.example frontend/.env.local && echo "  Created frontend/.env.local"
	@echo "$(GREEN)✓ Setup complete. Edit .env and add your API keys.$(RESET)"

install-backend: ## Install Python dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install Node.js dependencies
	cd frontend && npm install

install: install-backend install-frontend ## Install all dependencies

# ── Docker ───────────────────────────────────────────────────────────────────
up: ## Start all services with Docker Compose
	docker compose up -d --build
	@echo "$(GREEN)✓ Services starting..."
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs$(RESET)"

up-deps: ## Start only infrastructure (Postgres, Redis, Qdrant)
	docker compose up -d postgres redis qdrant

down: ## Stop all services
	docker compose down

down-volumes: ## Stop all services and remove volumes (destructive!)
	docker compose down -v

restart: ## Restart all services
	docker compose restart

logs: ## Follow logs from all services
	docker compose logs -f

logs-backend: ## Follow backend logs only
	docker compose logs -f backend

logs-frontend: ## Follow frontend logs only
	docker compose logs -f frontend

# ── Development ──────────────────────────────────────────────────────────────
dev-backend: ## Start backend in dev mode (hot reload)
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend in dev mode
	cd frontend && npm run dev

# ── Database ─────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new Alembic migration (usage: make migrate-new MSG="add column")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

migrate-history: ## Show migration history
	cd backend && alembic history --verbose

seed: ## Seed the database with sample data
	cd backend && python -c "
import asyncio
from database.session import get_db_context
from models.db_models import User
from core.security import get_password_hash

async def seed():
    async with get_db_context() as db:
        user = User(
            email='admin@researchai.com',
            username='admin',
            hashed_password=get_password_hash('admin123'),
            full_name='Admin User',
            role='admin',
        )
        db.add(user)
        print('Seeded admin user: admin@researchai.com / admin123')

asyncio.run(seed())
"

# ── Testing ──────────────────────────────────────────────────────────────────
test: ## Run all tests
	cd backend && pytest tests/ -v

test-unit: ## Run unit tests only
	cd backend && pytest tests/ -v -m unit

test-integration: ## Run integration tests only
	cd backend && pytest tests/ -v -m integration

test-coverage: ## Run tests with coverage report
	cd backend && pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# ── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Lint Python code
	cd backend && python -m flake8 . --max-line-length=100 --exclude=alembic,__pycache__

format: ## Format Python code with black
	cd backend && python -m black . --line-length=100 --exclude=alembic

type-check: ## Type check Python with mypy
	cd backend && python -m mypy . --ignore-missing-imports --exclude alembic

lint-frontend: ## Lint TypeScript/React code
	cd frontend && npm run lint

type-check-frontend: ## Type check frontend
	cd frontend && npm run type-check

# ── Build ────────────────────────────────────────────────────────────────────
build: ## Build Docker images
	docker compose build

build-backend: ## Build backend Docker image only
	docker build -t research-ai-backend ./backend

build-frontend: ## Build frontend Docker image only
	docker build -t research-ai-frontend ./frontend

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(RESET)"

clean-docker: ## Remove all project Docker containers and images
	docker compose down --rmi all -v --remove-orphans

# ── Info ─────────────────────────────────────────────────────────────────────
status: ## Show running service status
	docker compose ps

health: ## Check all service health endpoints
	@echo "$(CYAN)Backend:$(RESET)"
	@curl -sf http://localhost:8000/health | python -m json.tool || echo "  ✗ Backend not responding"
	@echo "$(CYAN)Frontend:$(RESET)"
	@curl -sf -o /dev/null -w "  Status: %{http_code}\n" http://localhost:3000 || echo "  ✗ Frontend not responding"
