# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning: [SemVer](https://semver.org/).

## [Unreleased]
### Added
- Project skeleton: FastAPI backend (Clean Architecture), React + TypeScript frontend, Docker Compose for dev/test/prod.
- `GET /api/health` endpoint and a backend status card in the UI.
- MIT license.
- OpenTelemetry traces, metrics and logs from the API, viewed in Grafana (`grafana/otel-lgtm`) or written to JSON Lines files (`SA_OTEL_EXPORTER=file`).
- **Phase 1 POC on synthetic data:**
  - Database: Alembic migrations 0001–0003 (TimescaleDB, pgvector, pgcrypto; 14 tables incl. the `prices_daily` hypertable); `make db-*` commands.
  - Redis key registry with enforced TTLs; `make redis-*` commands.
  - Domain: holding categories (50D–3Y), trading calendar, trade plan rules (prediction locked, outcome calculated with ±0.5 pp tolerance), empirical baseline prediction (no future data).
  - Mock provider: deterministic synthetic NIFTY 50 data (5 years, regimes, splits); `make seed`, `make predict`, `make poc-data`.
  - API: stocks, prices, predictions, trade plans (start/list/get/close), admin providers (list/test).
  - Web: stock search, candlestick chart with plan lines, predictions in the headline format, trade journal, providers page, SYNTHETIC DATA badge; shadcn/ui + Lightweight Charts.
  - Reproducible setup: `compose.devdata.yaml` and `make bootstrap` (fresh clone → running POC).

- **UI redesign (Phase 1b):** Kite-like design system (tokens, light/dark, Geist, tabular numbers, Lucide icons), app shell
  (sidebar, phone bottom nav, ⌘K search, live NSE status), Home dashboard, sortable Stocks table, Stock detail (themed
  chart with ranges, range-bar predictions, target odds), guided Start-plan sheet, Close dialog with outcome preview,
  Journal tabs with track record, Providers cards; skeleton/empty/error states; `npm run lint:ui` rule check; `make ui-shots`.
- API: `GET /api/stocks/overview`, `GET /api/trade-plans/summary`.

### Fixed
- Price chart blank when the browser locale is missing (explicit `en-IN` locale).
- Percentage-point differences shown as "% pp".
- Dev API replaced by test runs: tests now use their own compose project (`stock-analyzer-test`) and `--no-deps`.
- `make lint` failed on tool caches (`/app` owned by root in the dev image).
- Duplicate model versions when the category is NULL.
