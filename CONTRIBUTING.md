# Contributing

This is a portfolio project, but it's built to the same standard as a real codebase - contributions
and suggestions are welcome.

## Local development

**Full stack (Docker):**

```bash
cp .env.example .env
docker compose up -d --build
```

**Backend only, outside Docker** (useful for faster iteration):

```bash
cd backend
docker compose up -d postgres simulator   # dependencies still run in Docker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://autoops:autoops@localhost:5432/autoops
export SIMULATOR_URL=http://localhost:9000
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend only:**

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

## Project structure

```
backend/app/
  api/routes/     REST endpoints
  agents/         LLM provider abstraction + investigation prompts/schemas
  tools/          read-only (agent-facing) vs. mutating (remediation-only) tool implementations
  policies/       risk classification and approval-requirement logic
  services/       business logic orchestration (one file per concern)
  models/         SQLAlchemy ORM models
  schemas/        Pydantic API schemas (kept separate from ORM models on purpose)
  observability/  Prometheus metric definitions
simulator/app/    the checkout-service traffic/failure simulator
frontend/src/
  api/            typed API client functions + TypeScript types matching backend schemas
  hooks/          TanStack Query hooks
  components/     shared UI components
  pages/          the 5 dashboard pages
```

## Before submitting a change

```bash
# Backend
cd backend
ruff check app/ tests/
pytest -v          # needs `docker compose up -d postgres` running

# Frontend
cd frontend
npm run lint
npm run build       # also type-checks
npm run test
```

CI runs all of the above on every push and pull request.

## Code style

- Backend: typed Python, `ruff` for linting (config in `backend/pyproject.toml`). No comments
  explaining *what* code does - only *why*, when it's non-obvious.
- Frontend: TypeScript with `strict` mode on. No UI framework dependency - the design system is a
  handful of CSS variables and utility classes in `index.css`.
- No placeholder implementations. If something isn't built yet, it isn't in the codebase.

## Commit messages

Plain, descriptive, explain the *why* over the *what*. No fixed convention is enforced, but this
repo's own history is a good reference for the expected level of detail.
