# LocalMate 🗺️

Local community marketplace with AI-powered search, token economy, and gamified skill levels.

## Architecture

Microservices, each in its own Docker container:

| Service | Tech | Port | Role |
|---|---|---|---|
| `gateway` | FastAPI | 8000 | Single entry point, JWT validation, routing |
| `auth` | FastAPI | 8001 | Registration, login, JWT tokens |
| `users` | FastAPI | 8002 | Profiles, location, XP, levels |
| `search` | FastAPI | 8003 | Gemini AI + PostGIS geo-search |
| `tokens` | FastAPI | 8004 | Balance, transactions |
| `vendors` | FastAPI | 8005 | Public CRUD API for agents |
| `worker` | Celery | — | Background tasks (XP, notifications) |
| `frontend` | React+Vite | 3000 | UI |
| `postgres` | PostgreSQL+PostGIS | 5432 | Main database |
| `redis` | Redis | 6379 | Cache + Celery broker |

## Quick Start (local)

```bash
cp .env.example .env
# Fill in your GEMINI_API_KEY and SECRET_KEY
docker compose up --build
```

App available at: http://localhost:3000  
API docs: http://localhost:8000/docs

## Project Structure

```
localmate/
├── services/
│   ├── gateway/      # API gateway
│   ├── auth/         # Authentication
│   ├── users/        # User profiles & XP
│   ├── search/       # AI search
│   ├── tokens/       # Token economy
│   ├── vendors/      # Vendor API for agents
│   ├── worker/       # Celery worker
│   ├── frontend/     # React UI
│   └── shared/       # Shared models & utils
├── infra/
│   ├── terraform/    # AWS infrastructure
│   └── k8s/          # Kubernetes manifests
└── .github/
    └── workflows/    # CI/CD
```

## Deployment

See `infra/terraform/` for AWS deployment (ECS Fargate + RDS + ElastiCache).

## Scaling

All services are stateless and horizontally scalable.  
Designed for 5000+ concurrent users.
