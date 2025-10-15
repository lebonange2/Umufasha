# Makefile for Personal Assistant

.PHONY: help up down build test clean seed-demo logs

# Default target
help:
	@echo "Personal Assistant - Available Commands:"
	@echo ""
	@echo "  make up          - Start all services with Docker Compose"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Build Docker images"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make seed-demo   - Create demo user and events"
	@echo "  make logs        - Show logs from all services"
	@echo "  make dev         - Start development environment with ngrok"
	@echo ""

# Start all services
up:
	docker compose up -d

# Start with ngrok for development
dev:
	docker compose --profile dev up -d

# Stop all services
down:
	docker compose down

# Build Docker images
build:
	docker compose build

# Run tests
test:
	docker compose exec web pytest

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Create demo data
seed-demo:
	docker compose exec web python scripts/seed_demo.py

# Show logs
logs:
	docker compose logs -f

# Show logs for specific service
logs-web:
	docker compose logs -f web

logs-worker:
	docker compose logs -f worker

logs-db:
	docker compose logs -f db

# Database operations
db-shell:
	docker compose exec db psql -U assistant -d assistant

db-reset:
	docker compose exec web python -c "from app.database import engine; from app.models import Base; import asyncio; asyncio.run(engine.run_sync(Base.metadata.drop_all)); asyncio.run(engine.run_sync(Base.metadata.create_all))"

# Development helpers
install-dev:
	pip install -r requirements-app.txt

run-local:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	python -m app.worker

# Health checks
health:
	curl -f http://localhost:8000/health || echo "Service not healthy"

# Quick setup for new developers
setup: build up
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Creating demo data..."
	@make seed-demo
	@echo ""
	@echo "Setup complete! Visit http://localhost:8000/admin"
	@echo "Login: admin / admin123"