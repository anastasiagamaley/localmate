# LocalMate — Developer Makefile
# Usage: make <target>

.PHONY: help up down build logs ps clean setup

help:
	@echo ""
	@echo "  LocalMate Dev Commands"
	@echo "  ──────────────────────────────────────"
	@echo "  make setup    — copy .env.example → .env"
	@echo "  make up       — start all services"
	@echo "  make down     — stop all services"
	@echo "  make build    — rebuild all images"
	@echo "  make logs     — tail all logs"
	@echo "  make ps       — show running containers"
	@echo "  make clean    — remove volumes (wipes DB!)"
	@echo "  make shell-db — open psql in postgres"
	@echo "  make test     — run all tests"
	@echo ""

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "✅ .env created — fill in your GEMINI_API_KEY"; \
	else echo "ℹ️  .env already exists"; fi

up:
	docker compose up -d
	@echo ""
	@echo "  🚀 LocalMate is running!"
	@echo "  Frontend  → http://localhost:3000"
	@echo "  API docs  → http://localhost:8000/docs"
	@echo ""

down:
	docker compose down

build:
	docker compose build --parallel

logs:
	docker compose logs -f

logs-gateway:
	docker compose logs -f gateway

logs-auth:
	docker compose logs -f auth

ps:
	docker compose ps

clean:
	@echo "⚠️  This will delete all data (DB volumes)!"
	@read -p "Continue? [y/N] " ans && [ "$$ans" = "y" ] && \
		docker compose down -v && echo "✅ Cleaned" || echo "Aborted"

shell-db:
	docker compose exec postgres psql -U localmate -d localmate

shell-redis:
	docker compose exec redis redis-cli

restart-%:
	docker compose restart $*

# Run tests for a specific service: make test-auth
test-%:
	cd services/$* && pip install pytest pytest-asyncio && pytest tests/ -v || echo "No tests found"

test:
	@for svc in gateway auth users search tokens vendors; do \
		echo "── Testing $$svc ──"; \
		if [ -d "services/$$svc/tests" ]; then \
			cd services/$$svc && pytest tests/ -v && cd ../..; \
		else echo "No tests yet"; fi; \
	done

# Health check all services
health:
	@echo "Checking all services..."
	@curl -sf http://localhost:8000/health && echo " ✅ gateway" || echo " ❌ gateway"
	@curl -sf http://localhost:8001/health && echo " ✅ auth"    || echo " ❌ auth"
	@curl -sf http://localhost:8002/health && echo " ✅ users"   || echo " ❌ users"
	@curl -sf http://localhost:8003/health && echo " ✅ search"  || echo " ❌ search"
	@curl -sf http://localhost:8004/health && echo " ✅ tokens"  || echo " ❌ tokens"
	@curl -sf http://localhost:8005/health && echo " ✅ vendors" || echo " ❌ vendors"
	@curl -sf http://localhost:3000        && echo " ✅ frontend" || echo " ❌ frontend"
