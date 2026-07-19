.PHONY: help install install-backend install-frontend backend frontend \
        test test-all lint clean seed-demo setup-git format

help:
	@echo "Vayu-Drishti — Smart City Air Quality Intelligence Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install all dependencies (backend + frontend)"
	@echo "  make backend        Start the unified backend (localhost:8000)"
	@echo "  make frontend       Start the Next.js frontend (localhost:3000)"
	@echo "  make test           Run Python tests"
	@echo "  make lint           Run linters (ruff on Python, next lint on frontend)"
	@echo "  make clean          Clean temporary and generated files"
	@echo "  make seed-demo      Load demo data into the local database"
	@echo "  make setup-git      Configure Git hooks and repo settings"
	@echo ""

install: install-backend install-frontend

install-backend:
	pip install -e backend/
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

backend:
	python -m backend.main

frontend:
	cd frontend && npm run dev

test:
	python -m pytest tests/ -v --tb=short -x

test-all:
	python -m pytest tests/ backend/tests/ -v --tb=short -x

lint:
	cd frontend && npm run lint
	ruff check backend/ agents/ ingestion/ decision-engine/ knowledge-graph/ llm-service/ tests/ api-gateway/

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf backend/__pycache__ backend/src/__pycache__
	rm -rf backend/src/agents/__pycache__
	rm -rf backend/src/agents/*/__pycache__
	rm -rf backend/src/agents/*/**/__pycache__
	rm -rf backend/src/api/__pycache__
	rm -rf backend/src/decision_engine/__pycache__
	rm -rf backend/src/infrastructure/__pycache__
	rm -rf backend/src/ingestion/__pycache__
	rm -rf backend/src/ingestion/*/__pycache__
	rm -rf backend/src/knowledge_graph/__pycache__
	rm -rf backend/src/llm_service/__pycache__
	rm -rf tests/__pycache__
	rm -rf agents/*/__pycache__ agents/*/src/__pycache__ agents/*/src/**/__pycache__
	rm -rf ingestion/src/__pycache__ ingestion/src/*/__pycache__
	rm -rf knowledge-graph/src/__pycache__
	rm -rf *.egg-info backend/*.egg-info
	@echo "Cleaned project artifacts."

seed-demo:
	python deploy/seed_demo.py

setup-git:
	git config core.hooksPath .githooks || true
	git config core.autocrlf input
	@echo "Git hooks configured. Run 'make install' to set up dependencies."
