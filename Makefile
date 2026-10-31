DEV  := docker compose -f compose.yaml -f compose.dev.yaml --profile telemetry
DEV_FILE := SA_OTEL_EXPORTER=file docker compose -f compose.yaml -f compose.dev.yaml
TEST := docker compose -f compose.yaml -f compose.test.yaml
PROD := docker compose -f compose.yaml -f compose.prod.yaml --profile telemetry

# Standalone dev containers (run outside compose), reached by the api as db / redis.
DEV_NET         := stock-analyzer-devdata
DB_CONTAINER    ?= timescaledb
REDIS_CONTAINER ?= RedisDev

.PHONY: help setup dev-network dev dev-file dev-data infra down prod test lint format api-client logs

help:          ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

setup:         ## Local (non-Docker) install: backend venv + frontend node_modules + git hooks
	cd backend && python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
	cd frontend && npm install
	backend/.venv/bin/pip install pre-commit && backend/.venv/bin/pre-commit install

dev-network:   ## Shared network: timescaledb -> db, RedisDev -> redis (safe to re-run)
	@docker network inspect $(DEV_NET) >/dev/null 2>&1 || docker network create $(DEV_NET)
	@docker network connect --alias db $(DEV_NET) $(DB_CONTAINER) 2>/dev/null || true
	@docker network connect --alias redis $(DEV_NET) $(REDIS_CONTAINER) 2>/dev/null || true

dev: dev-network  ## api + web + telemetry with hot reload (web :5173, api :8000, Grafana :3000)
	$(DEV) up --build

dev-file: dev-network  ## api + web only; telemetry written to ./telemetry/*.jsonl (no Grafana)
	$(DEV_FILE) up --build

dev-data: dev-network  ## Same as dev, plus compose's own db + redis (stop timescaledb first: both use :5432)
	$(DEV) --profile data up --build

infra:         ## db + redis + telemetry in Docker (for running api/web from VS Code)
	$(DEV) --profile data up -d db redis otel-lgtm

down:          ## Stop all containers
	$(DEV) --profile data down

prod:          ## Production stack (web :8080)
	$(PROD) up -d --build

test:          ## pytest + Vitest in containers
	$(TEST) run --rm --build api
	$(TEST) run --rm --build web

lint:          ## ruff, mypy, import-linter, ESLint, Prettier in containers
	$(TEST) run --rm --build api sh -c "ruff check . && ruff format --check . && mypy src tests && lint-imports"
	$(TEST) run --rm --build web npm run lint

format:        ## Auto-format backend and frontend
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
	cd frontend && npm run format

api-client:    ## Regenerate the TypeScript API client (api must be running on :8000)
	cd frontend && npm run api-client

logs:          ## Follow container logs
	$(DEV) logs -f
