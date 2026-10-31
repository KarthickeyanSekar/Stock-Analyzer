# Stock Analyzer

Short- and long-term stock analysis for NSE/BSE: data collection, screening, predictions and a trade journal.
Planning docs live in [docs/](docs/README.md).

**Stack:** FastAPI (Clean Architecture) · React + TypeScript (Vite) · PostgreSQL + TimescaleDB · Redis · Docker Compose.

## Quick start (Docker)
```bash
git clone https://github.com/KarthickeyanSekar/Stock-Analyzer.git && cd Stock-Analyzer
make bootstrap  # once: .env + secrets, PostgreSQL + Redis, migrations, synthetic POC data + predictions
make dev        # open http://localhost:5173/stocks · api http://localhost:8000/docs · Grafana :3000
make down       # stop the app (database + Redis keep running; make dev-db-stop stops them)
```
POC walkthrough (synthetic data): [docs/deliverables/phase-01-demo.md](docs/deliverables/phase-01-demo.md). Reload data: `make poc-data`.
Database: `make db-upgrade`, `make db-revision m="…"`, `make db-shell`. Redis: `make redis-keys`, `make redis-info`.
Rules: [docs/17-database-backend.md](docs/17-database-backend.md#database-change-control).

## Telemetry (OpenTelemetry)
The API records traces, metrics and logs with OpenTelemetry. Nothing leaves your machine. Pick where they go:

| Mode | Start with | Where to look |
|---|---|---|
| **Grafana** (`SA_OTEL_EXPORTER=otlp`) | `make dev` | http://localhost:3000 (admin / admin) → **Explore**: Tempo = traces, Prometheus = metrics, Loki = logs |
| **Files** (`SA_OTEL_EXPORTER=file`) | `make dev-file` | `telemetry/traces.jsonl`, `metrics.jsonl`, `logs.jsonl` (one JSON object per line) |

File mode needs no extra container. Read it with e.g. `tail -f telemetry/logs.jsonl | jq .body`.
Turn telemetry off completely with `SA_OTEL_ENABLED=false` in `.env`.

## Run from VS Code
1. Install the recommended extensions when prompted.
2. Run task **Setup: install backend + frontend** (or `make setup`) once. Needs Python 3.12 and Node 22+.
3. Optional: `make infra` to start PostgreSQL, Redis and Grafana in Docker. To send telemetry from VS Code,
   set `SA_OTEL_ENABLED` to `true` in [.vscode/launch.json](.vscode/launch.json).
4. Run and Debug (⇧⌘D) → **Full stack (backend + frontend)** → F5.
   Open http://localhost:5173. Breakpoints work in the Python code; use **Full stack + Chrome debugging** to also debug React.

## Common commands
| Command | What it does |
|---|---|
| `make dev` | api + web + Grafana in Docker with hot reload |
| `make dev-file` | api + web only, telemetry to `./telemetry/` files |
| `make test` | pytest + Vitest in containers |
| `make lint` | ruff, mypy, import-linter, ESLint, Prettier |
| `make api-client` | Regenerate the typed TS client from the backend's OpenAPI |
| `make prod` | Production build on http://localhost:8080 |

## License
[MIT](LICENSE)
