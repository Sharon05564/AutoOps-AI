.PHONY: up down build logs reset demo backend-shell backend-test backend-lint frontend-test frontend-lint migrate

up: ## Start the full stack
	docker compose up -d --build

down: ## Stop the full stack
	docker compose down

build: ## Rebuild all images
	docker compose build

logs: ## Tail logs from every service
	docker compose logs -f

demo: ## Trigger the bad-deployment demo scenario
	curl -s -X POST http://localhost:8000/api/simulator/deployments/bad | python3 -m json.tool

reset: ## Reset the simulator and wipe incident history
	curl -s -X POST http://localhost:8000/api/simulator/reset | python3 -m json.tool

migrate: ## Run backend database migrations
	docker compose exec backend alembic upgrade head

backend-shell: ## Open a shell in the running backend container
	docker compose exec backend /bin/sh

backend-test: ## Run backend tests (requires: docker compose up -d postgres)
	cd backend && python -m pytest -v

backend-lint: ## Lint the backend
	cd backend && ruff check app/ tests/

frontend-test: ## Run frontend tests
	cd frontend && npm run test

frontend-lint: ## Lint the frontend
	cd frontend && npm run lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
