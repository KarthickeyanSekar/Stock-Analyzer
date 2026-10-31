DEV  := docker compose -f compose.yaml -f compose.dev.yaml --profile telemetry
DEV_FILE := SA_OTEL_EXPORTER=file docker compose -f compose.yaml -f compose.dev.yaml
TEST := docker compose -f compose.yaml -f compose.test.yaml
PROD := docker compose -f compose.yaml -f compose.prod.yaml --profile telemetry
# Dev database + Redis: their own compose project (compose.devdata.yaml), so `make down` never stops them.
DEVDATA := docker compose -f compose.devdata.yaml
# One-off command in the api image with the source mounted (alembic, scripts).
API_RUN := $(DEV) run --rm --no-deps api
# Batch jobs: no telemetry export (nothing to trace for a one-off CLI run).
JOB_RUN := $(DEV) run --rm --no-deps -e SA_OTEL_ENABLED=false api

DEV_NET         := stock-analyzer-devdata
DB_CONTAINER    ?= timescaledb
REDIS_CONTAINER ?= RedisDev
# Load SA_* values from .env into a recipe's shell (each recipe line runs in its own shell).
LOAD_ENV := set -a; . ./.env; set +a

.PHONY: help bootstrap setup dev-db dev-db-stop dev-network dev dev-file dev-data infra down prod \
        test lint format api-client logs ui-shots \
        seed predict poc-data db-upgrade db-downgrade db-revision db-current db-history db-shell db-reset \
        redis-shell redis-info redis-keys redis-flush

help:          ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

# --- Setup -------------------------------------------------------------------------------

bootstrap:     ## Fresh clone: create .env + secrets, start db + redis, run migrations (safe to re-run)
	sh scripts/bootstrap-dev.sh

setup:         ## Local (non-Docker) install: backend venv + frontend node_modules + git hooks
	cd backend && python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
	cd frontend && npm install
	backend/.venv/bin/pip install pre-commit && backend/.venv/bin/pre-commit install

dev-db:        ## Start the dev database (timescaledb -> db) and Redis (RedisDev -> redis)
	@docker network inspect $(DEV_NET) >/dev/null 2>&1 || docker network create $(DEV_NET)
	$(DEVDATA) up -d --wait

dev-db-stop:   ## Stop the dev database and Redis (data stays in the volumes)
	$(DEVDATA) stop

dev-network: dev-db  ## Alias of dev-db (kept for older docs and scripts)

# --- Run ---------------------------------------------------------------------------------

dev: dev-db    ## api + web + telemetry with hot reload (web :5173, api :8000, Grafana :3000)
	$(DEV) up --build

dev-file: dev-db  ## api + web only; telemetry written to ./telemetry/*.jsonl (no Grafana)
	$(DEV_FILE) up --build

dev-data:      ## api + web + compose's own db + redis (stop the dev-db stack first: both use :5432)
	@docker network inspect $(DEV_NET) >/dev/null 2>&1 || docker network create $(DEV_NET)
	$(DEV) --profile data up --build

infra:         ## compose's own db + redis + telemetry (for running api/web from VS Code)
	$(DEV) --profile data up -d db redis otel-lgtm

down:          ## Stop the app containers (the dev-db stack keeps running)
	$(DEV) --profile data down

prod:          ## Production stack (web :8080)
	$(PROD) up -d --build

logs:          ## Follow container logs
	$(DEV) logs -f

# --- Quality -----------------------------------------------------------------------------

test:          ## pytest + Vitest in containers
	$(TEST) run --rm --build api
	$(TEST) run --rm --build --no-deps web

lint:          ## ruff, mypy, import-linter, ESLint, Prettier in containers
	$(TEST) run --rm --build api sh -c "ruff check . && ruff format --check . && mypy src tests && lint-imports"
	$(TEST) run --rm --build --no-deps web npm run lint

format:        ## Auto-format backend and frontend (in containers, writes to the mounted source)
	$(API_RUN) sh -c "ruff format . && ruff check --fix ."
	$(DEV) run --rm --no-deps web npm run format

ui-shots:      ## Screenshots of every screen (light, dark, phone) into frontend/screenshots; app must be running
	docker run --rm --network container:stock-analyzer-web-1 -v "$(CURDIR)/frontend:/work" -w /work \
	  mcr.microsoft.com/playwright:v1.49.1-noble sh -c "npm i --no-save --silent playwright@1.49.1 && node scripts/ui-screenshots.mjs"

api-client:    ## Regenerate the TypeScript API client (api must be running on :8000)
	cd frontend && npm run api-client

# --- Data jobs (POC: synthetic data) ------------------------------------------------------

seed:          ## Load synthetic NIFTY 50 data (mock provider, 5 years); safe to re-run
	$(JOB_RUN) python -m stock_analyzer.presentation.jobs.seed

predict:       ## Compute baseline predictions for every stock and holding category
	$(JOB_RUN) python -m stock_analyzer.presentation.jobs.predict

poc-data: seed predict  ## POC data in one step: seed + predict (run after db-upgrade)

# --- PostgreSQL (schema changes only through Alembic migrations) -------------------------

db-upgrade:    ## Apply all pending migrations
	$(API_RUN) alembic upgrade head

db-downgrade:  ## Revert the last migration
	$(API_RUN) alembic downgrade -1

db-revision:   ## New migration from model changes: make db-revision m="add trade plans" id=0004
	@[ -n "$(m)" ] && [ -n "$(id)" ] || { echo 'Usage: make db-revision m="short description" id=<next 4-digit number>'; exit 1; }
	$(API_RUN) alembic revision --autogenerate --rev-id "$(id)" -m "$(m)"

db-current:    ## Show the database's current migration
	$(API_RUN) alembic current -v

db-history:    ## List all migrations
	$(API_RUN) alembic history -v

db-shell:      ## psql inside the dev database container
	@$(LOAD_ENV); docker exec -it $(DB_CONTAINER) psql -U "$$SA_DB_USER" -d "$$SA_DB_NAME"

db-reset:      ## DEV ONLY: drop + recreate the dev database, then migrate (asks for confirmation)
	@$(LOAD_ENV); [ "$$SA_ENV" = "dev" ] || { echo "db-reset only runs with SA_ENV=dev"; exit 1; }; \
	printf 'This DELETES all data in %s. Type RESET to continue: ' "$$SA_DB_NAME"; read answer; \
	[ "$$answer" = "RESET" ] || { echo "Cancelled."; exit 1; }; \
	docker exec $(DB_CONTAINER) psql -U "$$SA_DB_USER" -d postgres -v ON_ERROR_STOP=1 \
	  -c "DROP DATABASE IF EXISTS \"$$SA_DB_NAME\" WITH (FORCE)" -c "CREATE DATABASE \"$$SA_DB_NAME\""
	$(MAKE) db-upgrade

# --- Redis (no schema: keys are defined in infrastructure/cache/keys.py) -----------------

redis-shell:   ## redis-cli inside the dev Redis container
	docker exec -it $(REDIS_CONTAINER) redis-cli

redis-info:    ## Memory, key count and persistence status
	@docker exec $(REDIS_CONTAINER) redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_policy'
	@docker exec $(REDIS_CONTAINER) redis-cli INFO persistence | grep -E 'rdb_last_save_time|aof_enabled'
	@docker exec $(REDIS_CONTAINER) redis-cli INFO keyspace

redis-keys:    ## List keys safely with SCAN: make redis-keys p="sa:dev:*"
	docker exec $(REDIS_CONTAINER) redis-cli --scan --pattern "$(or $(p),sa:dev:*)"

redis-flush:   ## DEV ONLY: delete this environment's keys (sa:<env>:*), never the whole server
	@$(LOAD_ENV); [ "$$SA_ENV" = "dev" ] || { echo "redis-flush only runs with SA_ENV=dev"; exit 1; }; \
	printf 'Delete all sa:%s:* keys? Type FLUSH to continue: ' "$$SA_ENV"; read answer; \
	[ "$$answer" = "FLUSH" ] || { echo "Cancelled."; exit 1; }; \
	docker exec $(REDIS_CONTAINER) sh -c "redis-cli --scan --pattern 'sa:$$SA_ENV:*' | xargs -r redis-cli DEL"
