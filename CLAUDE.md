# CLAUDE.md

Instructions for Claude when working in this repository. Humans: start with [README.md](README.md) and [docs/README.md](docs/README.md).

## Project in one paragraph
Stock Analyzer predicts how much an NSE stock may return over a chosen **holding category**
(50D · 100D · 200D · 300D · 1Y · 2Y · 3Y) and lets users track plans in a **manual trade journal**.
India (NSE; BSE optional) now, world markets later, so keep code **market-agnostic** (market, currency, timezone, calendar per stock).
**Long-term is built first**; short-term (1 day – 2 weeks) comes later. Current phase: **Phase 1 – Foundation, as a POC on synthetic data** ([docs/27-phase1-poc-plan.md](docs/27-phase1-poc-plan.md)).
Synthetic records use `source_provider = "mock"` and the UI shows a SYNTHETIC badge; never present them as real prices.

## Non-negotiable product rules
- **Predictions are pure statistics / ML.** An LLM never produces a number (prices, %, probabilities). OpenAI is optional, for explanations only.
- **Every prediction has a range and a probability**, never a single certain number. Headline format: `+9% (−6…+24%) · 41% chance of +20%`.
- **No broker, no orders.** The app never places trades. Journal values are entered manually; prices and fundamentals come from data-only APIs.
- **No scrapers, bhavcopy parsers or unofficial data libraries** (yfinance, jugaad-data …). Only managed APIs through provider plugins.
- **Provider credentials are configured in the admin UI** and stored encrypted (Fernet, `SA_MASTER_KEY`). `.env` holds bootstrap values only.
- Journal rules: one start, one planned end, one exit; prediction **locked** at start; outcome **calculated**
  (equal within tolerance = SUCCESS, above = PARTIAL + tuning required, below = FAILURE; default tolerance ±0.5 pp).
- Money and percentages use `Decimal`-based value objects, never floats. Datetimes are timezone-aware; store UTC, display in market time.

## Architecture (enforced by import-linter)
Backend: `backend/src/stock_analyzer/` in Clean Architecture layers. Dependencies point **inwards only**:
`presentation → infrastructure → application → domain`.
- `domain/`: pure Python business rules (entities, value objects, calculators). **No** fastapi, sqlalchemy, pydantic, redis, apscheduler, opentelemetry.
- `application/`: use cases (`VerbNoun.execute()`) and **ports** (ABC interfaces).
- `infrastructure/`: adapters (SQLAlchemy repositories, provider plugins, security, telemetry, config).
- `presentation/`: FastAPI routers/schemas and job entry points. Wiring only in `bootstrap.py`.
Frontend: **kebab-case file names, PascalCase component names**. `frontend/src/` is feature-based (`app/`, `pages/`, `features/<feature>/`, `shared/`). Features import each other only via `index.ts`.
UI uses **shadcn/ui + Tailwind 4** (components in `shared/ui/`). Server data only via TanStack Query; no business maths in the UI.

Full rules, naming tables and examples: [docs/24-coding-standards.md](docs/24-coding-standards.md). Follow them exactly.

## Frontend UI rules (enforced by `npm run lint` where possible)
Direction (Q58–Q61): **Kite-like** (clean, minimal, fast, data-dense; the feel only, never Zerodha's brand or assets), modern,
smooth motion, responsive (phone, tablet, desktop). Full spec: [docs/28-ui-ux-redesign-plan.md](docs/28-ui-ux-redesign-plan.md).
- **Tokens only:** colours come from CSS variables in `src/index.css` (`background`, `foreground`, `card`, `muted`, `primary`,
  `border`, plus `gain`, `loss`, `warning`, `synthetic`). No raw palette classes (`slate-500`), no hex in `app/`, `pages/`, `features/`.
- **Icons:** Lucide only. **No emoji** in UI text. Icon-only buttons need `aria-label`.
- **Numbers:** `tabular-nums` everywhere; money via `formatInr`, % via `formatPct` (sign + true minus); gain/loss always has a sign
  or arrow as well as colour (never colour alone).
- **Components:** shadcn/ui in `shared/ui` (Sheet, Dialog, Tooltip, Skeleton, Sonner toast, Progress, Command …). No native
  `<select>` or hand-rolled modals. Plans start in a **Sheet**; closing a plan uses a **Dialog** with an outcome preview.
- **States:** every data view has skeleton, empty (icon + sentence + action) and error (message + retry) states.
- **Motion:** 150–250 ms, ease-out in / ease-in out; animate to explain change (sheet slide, dialog fade-scale, bars grow, stagger);
  always respect `prefers-reduced-motion` (use the `motion-safe:` variant).
- **Responsive:** phone < 640 px (bottom nav, stacked cards, tables as cards), tablet, desktop (sidebar). Touch targets ≥ 40 px.
- **Theme:** light + dark via the `dark` class (follows the system, user toggle remembered).
- **Verify visually:** after UI changes run `make e2e` (visual baselines) and `make ui-shots`; look at the screenshots. Intended changes: `make e2e-update`, review, commit the PNGs.

## Naming (short version)
Python: `snake_case` modules/functions, `PascalCase` classes, ports named by role (`MarketDataProvider`),
implementations prefixed by technology/vendor (`SqlAlchemyTradePlanRepository`, `EodhdMarketDataProvider`),
errors end in `Error`, booleans `is_/has_/can_`, units as suffixes (`target_pct`, `latency_ms`), `…_date` vs `…_at`.
DB: plural `snake_case` tables, `<singular>_id` FKs. API: `/api/<plural-kebab>`. Env vars: `SA_` prefix.

## Commands (everything runs in Docker)
| Command | Use |
|---|---|
| `make dev` | api + web + Grafana with hot reload (runs `make dev-network` first) |
| `make test` | pytest (incl. DB integration tests on a throwaway TimescaleDB) + Vitest in containers |
| `make e2e` | Playwright browser + visual regression tests on a throwaway seeded stack (never touches dev data) |
| `make e2e-update` | Re-record visual baselines after an intended UI change; review the PNGs before committing |
| `make lint` | ruff, ruff format, mypy (strict), import-linter, ESLint/Prettier in containers |
| `make api-client` | Regenerate the TS client after any API change |
| `make bootstrap` | Fresh clone: `.env` + secrets, db + Redis, migrations |
| `make dev-db` | Start the dev database + Redis (`compose.devdata.yaml`) |
| `make db-upgrade` / `db-revision m="…"` / `db-downgrade` / `db-current` / `db-shell` | Database migrations and access |
| `make redis-shell` / `redis-keys` / `redis-info` | Redis access |
| `make ui-shots` | Screenshots of every screen (light, dark, phone) into `frontend/screenshots/`; review them after UI changes |
| `make seed` / `make predict` / `make poc-data` | POC data: synthetic NIFTY 50 (mock provider) + baseline predictions |
| `make track` | Daily progress snapshots of active journal plans (`plan_daily_status`) |
| `make validate` | Phase 5: point-in-time backtest (net of costs/tax), calibration, journal review, go/no-go → `docs/reports/validation.md` |
| `make real-data` | After an EODHD key is saved and set primary in Admin › Providers: replace synthetic data with real NSE data (asks first), then rebuild ML |
| `make features` / `make train` / `make ml-data` / `make model-rollback c=1Y` | ML engine: point-in-time features + labels, train/evaluate/gate (report in `docs/reports/`), whole pipeline, rollback |
URLs: web http://localhost:5173 · api http://localhost:8000/docs · Grafana http://localhost:3000.
The Makefile must stay compatible with **GNU Make 3.81** (macOS default): no `.ONESHELL` or newer functions.

## Local infrastructure (dev): everything is in the repo
- Fresh clone: `make bootstrap` (creates `.env` + secrets, starts db + Redis, runs migrations), then `make dev`.
- Dev database + Redis are defined in **`compose.devdata.yaml`**, a separate compose project, so `make down` never stops them.
  Start/stop with `make dev-db` / `make dev-db-stop`. Never create dev containers by hand: change the compose file instead.
- PostgreSQL = container **`timescaledb`** (`timescale/timescaledb-ha:pg16.15-ts2.31.0`, volume `timescale_data`), host **`db`**.
  Redis = container **`RedisDev`** (`redis:7.4.12-alpine3.21`, volume `redis_data`), host **`redis`**. Network `stock-analyzer-devdata`.
- **Never use the `-oss` TimescaleDB image**: it can't load the TSL library and `CREATE EXTENSION timescaledb` breaks the database.
- Compose projects are separate: `stock-analyzer` (app), `stock-analyzer-devdata` (db + Redis), `stock-analyzer-test` (tests),
  so `make test`/`make lint` never replace the running dev containers. Frontend test/lint runs use `--no-deps`.
- The api reads `.env` only when its container is created: after editing `.env`, recreate it
  (`docker compose -f compose.yaml -f compose.dev.yaml --profile telemetry up -d --no-deps --force-recreate api`).
- Never print, log or commit secrets (`.env`, `SA_MASTER_KEY`, DB passwords). Mask them in any command output.

## Database change control
**PostgreSQL: Alembic migrations only** (`backend/alembic.ini`, `infrastructure/persistence/migrations/versions/NNNN_*.py`).
1. Change the models in `infrastructure/persistence/models/` (import new models in `models/__init__.py`).
2. `make db-revision m="…"`, then **review** the file: autogenerate misses hypertables, pgvector indexes and extensions (add with `op.execute`).
3. `make db-upgrade`, then check `make db-downgrade` + `make db-upgrade` round-trips, and `alembic check` reports no drift.
4. Commit the model and its migration together. **Never edit a merged migration**: fix forward with a new one.
5. Never change the schema by hand (psql, GUI tools). `make db-shell` is for reading; `make db-reset` is dev only.
- Migration IDs are sequential (`0001`, `0002`, …): pass `--rev-id` with the next number when autogenerate picks a random one.
**Redis: no schema.** Every key is defined in `infrastructure/cache/keys.py` (`sa:{env}:{version}:…`); never build keys elsewhere.
Every cache/lock/rate-limit key has a TTL (enforced by a unit test); only job queues may have none. A format change = new version (`v2`).
Use `make redis-keys`, `make redis-info`; `make redis-flush` deletes only `sa:<env>:*` keys and only in dev.

## Testing and quality
- No CI: `make lint` and `make test` (in containers) plus pre-commit hooks are the only gate. Run both before declaring work done.
- Domain/application code gets unit tests (fake ports, no I/O); repositories/providers get integration tests with recorded fixtures.
- Include a data-leakage test for anything that builds features or labels (no future data).
- Definition of Done: [docs/24-coding-standards.md](docs/24-coding-standards.md#9-definition-of-done-every-change).

## Git workflow
- `master` is the stable branch. It changes **only by merging a PR from `develop`**; never commit or push to `master` directly.
- `develop` is the integration branch. New work goes on `feature/<short-name>` or `fix/<short-name>` from `develop`,
  merged back into `develop` by PR.
- Remote: `origin` = github.com/KarthickeyanSekar/Stock-Analyzer. PRs use the GitHub CLI (`gh`).
- Conventional Commits: `feat(journal): …`, `fix(providers): …`, `docs: …`, `chore: …`.
- Commit or push only when the user asks.

## Documentation rules
- **Deliverables & outcomes** live in `docs/deliverables/` (one `phase-NN-*.md` per phase, from `TEMPLATE.md`). Before starting a deliverable, read its outcome and acceptance criteria; when finishing, record the evidence and set its status. Never mark ✅ without evidence for every criterion.
- Planning docs live in `docs/NN-name.md`. Use the **`/plan-doc` skill** when adding or restructuring docs.
- **Append, never renumber:** a new doc gets the next number (`max(NN) + 1`); existing docs are never renamed or renumbered (keeps links and git history intact).
- The **decision log** is `docs/decisions/open-questions.md` (not numbered, stable path). New questions are appended with the next Q number.
- Diagrams are always **Mermaid**. Every doc has top and bottom nav bars and a Related section; the README index lists every doc.
- When a decision is made, record it as ✅ in `docs/decisions/open-questions.md` **and** update every doc it affects. Keep the docs matching the code.

## Sign-in (Phase 5b)
- Every API except `/api/health` and `/api/auth/*` needs a session; admin APIs need the admin role.
- Locally: `SA_DEV_LOGIN=true`; `SA_ADMIN_EMAILS` (default dev account `admin@stockanalyzer.com`, plus the owner's
  email) are admins and appear as one-click "Sign in as …" buttons (dev only, refused in prod). Real Google /
  Microsoft sign-in appears once their OAuth client id/secret are in `.env`.
- Roles: a **user** gets the whole app except Admin › Providers and Admin › Users (hidden, redirected, API 403);
  an **admin** gets everything. Each user sees only their own journal, settings and watchlist.
- Profile: Account menu › Profile (`/profile`): name, email, provider, role, dates, sign out, delete account.
- Tests: API test clients sign in with `tests.conftest.sign_in`; Playwright fixtures sign in as `admin@e2e.local`.

## Working with the user
- The user writes quickly and informally. Restate the interpretation when a request is ambiguous, and ask before anything hard to undo
  (deleting containers or volumes, recreating databases, force operations).
- Explain options as a comparison table with a recommendation, then record the decision in the docs.
