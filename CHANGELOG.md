# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning: [SemVer](https://semver.org/).

## [Unreleased]
- **Phase 3 – Long-term engine:** data-point calculators (doc 21 coverage table), point-in-time feature store `fs-v1` + triple-barrier labels (migration 0005), LightGBM quantile + calibrated target-probability models per category, split-conformal ranges, purged walk-forward evaluation vs universe and momentum baselines, Q51 quality gates, model registry with one-ACTIVE rule and rollback; `make features`, `make train`, `make model-rollback`, `make ml-data`. Decisions Q50, Q51, Q64.
- **Phase 2 – Trade journal (signed off 2026-11-01):**
  - Decisions Q28 (calendar days), Q29 (close, editable; `reference_close` + `entry_source`), Q31 (own target; outcome judged on the locked `predicted_pct`), Q63 (app-wide settings).
  - Plan progress from EOD candles (day N of M, return, stop → target bar) with target / stop / end-date flags; `make track` daily snapshots (migration 0004).
  - Settings page + `GET`/`PUT /api/settings/journal`; `POST /api/trade-plans/preview` (server-side position sizing).
  - Track record: success rate per category, actual vs predicted per plan, hit rate of your own targets.
- **Phase 1 (POC on synthetic data) and Phase 1b (UI redesign) signed off 2026-11-01.**

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
- **POC completion:** `FundamentalsProvider` port + synthetic quarterly fundamentals (point-in-time), `GET /api/stocks/{symbol}/fundamentals`;
  DB integration tests on a throwaway TimescaleDB inside `make test`; `make e2e` (Playwright on a throwaway seeded stack);
  response examples on every API model; pre-commit hooks installed.
- `Money` / `Percentage` value objects; Button render test; WCAG AA contrast audit of the tokens;
  visual regression baselines (`make e2e`, `make e2e-update`).

### Fixed
- Visual regression used a 1% pixel ratio, too loose to notice a changed number; now a 50-pixel budget.
- Dev Vite reloaded every open page while tests wrote results into the mounted source.
- Phone bottom navigation wrapped onto two rows with five items.
- ⌘K palette crashed the app on open (cmdk input rendered without a `<Command>` root).
- Journal tab panel had no visible keyboard focus ring.
- Plan dates shown as raw ISO (`2027-11-01`) in journal cards, the closed list and the start toast.
- Price chart blank when the browser locale is missing (explicit `en-IN` locale).
- Percentage-point differences shown as "% pp".
- Dev API replaced by test runs: tests now use their own compose project (`stock-analyzer-test`) and `--no-deps`.
- `make lint` failed on tool caches (`/app` owned by root in the dev image).
- Duplicate model versions when the category is NULL.
