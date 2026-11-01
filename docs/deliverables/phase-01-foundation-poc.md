[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [Next phase →](phase-01b-ui-redesign.md)

# Phase 1 – Foundation (POC on synthetic data)

**Phase outcome:** with `make dev`, a user can search a NIFTY 50 stock, see its price chart and a baseline prediction for every
holding category, start a journal plan, close it and see the outcome calculated. Everything runs on **synthetic data** behind the
real provider ports, so switching to a real API later needs no code changes outside a new plugin.

**Status:** 🟢 Built and verified, awaiting your sign-off · **Branch:** `feature/phase1-foundation` … `feature/phase1-finish` · **Plan:** [27 – Phase 1 POC Plan (Synthetic Data) 🧪](../27-phase1-poc-plan.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D1.0 | Tooling | Quality checks run automatically and pass before any feature code is added | ✅ |
| D1.1 | Database schema | The POC tables exist in `dev_stock_analyzer` and can be created and rolled back by migrations | 🟡 Clean-machine run / sign-off |
| D1.2 | Domain core | Money, percentages, holding categories, the trading calendar and the journal rules behave correctly and are proven by tests | ✅ |
| D1.3 | Synthetic data + mock provider | 5 years of realistic, repeatable NIFTY 50 data is loaded through the real provider ports | ✅ |
| D1.4 | Baseline predictions | Every stock has a prediction (range + target probabilities) for every holding category, with no future data used | ✅ |
| D1.5 | API | All POC features are available through documented, tested REST endpoints | ✅ |
| D1.6 | Frontend | The full POC flow works in the browser, clearly labelled as synthetic data | ✅ |
| D1.7 | Wrap-up | The POC is demonstrable, documented and merged into `develop` | 🟡 Clean-machine run / sign-off |

---

### D1.0 – Tooling
**Outcome:** every commit is checked automatically (lint, types, layer rules, secrets) and the test suite runs green in containers.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | pre-commit hooks installed and run on commit | `pre-commit run --all-files` passes | ✅ 2026-11-01: hooks installed in `backend/.venv`; `pre-commit run --all-files` passes (ruff, mypy, import-linter, ESLint/Prettier, gitleaks) |
| 2 | Lint, format, mypy (strict), import-linter, ESLint pass | `make lint` exits 0 | ✅ 2026-10-31 (after Dockerfile cache fix) |
| 3 | Backend and frontend tests pass | `make test` exits 0 | ✅ 2026-10-31 |
| 4 | shadcn/ui initialised with Tailwind 4 | `frontend/components.json` exists; a Button renders in a test | ✅ 2026-11-01: 22 components in `shared/ui`; `button.test.tsx` renders, clicks, disabled |
| 5 | Frontend file naming decided (Q55) and doc 24 updated | Q55 ✅ in Open Questions | ✅ 2026-10-31 |

---

### D1.1 – Database schema
**Outcome:** the POC tables exist and are managed only by Alembic migrations.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Tables: `markets`, `stocks`, `prices_daily`, `fundamentals`, `corporate_actions`, `predictions`, `model_versions`, `trade_plans`, `plan_daily_status`, `providers`, `provider_assignments`, `job_runs` | `alembic upgrade head` succeeds; `\dt` lists them | ✅ 2026-10-31: migrations 0001-0003, 14 tables |
| 2 | `prices_daily` is a TimescaleDB hypertable | `select * from timescaledb_information.hypertables` shows it | ✅ 2026-10-31 |
| 3 | Market-agnostic columns present (`market`, `currency`, `timezone` on stocks) | Schema test | ✅ 2026-10-31: `market_code`, `currency`, `timezone` on `stocks` (migration 0002) |
| 4 | Migrations roll back cleanly | `alembic downgrade base` then `upgrade head` succeed | ✅ 2026-10-31 (round trip on `dev_stock_analyzer`) |
| 5 | Repository integration tests pass against a throwaway DB | `make test` (integration) | ✅ 2026-11-01: `tests/integration/test_database.py` (7 tests) on a throwaway TimescaleDB in `make test`: migration round trip + `alembic check`, hypertable, idempotent backfill, exact Decimal round trip, point-in-time fundamentals, predictions, plan lifecycle |
| 6 | Alembic configured; `make db-*` commands work | `make db-upgrade` / `db-current` → `0002 (head)` | ✅ 2026-10-31: 0001 extensions, 0002 markets/stocks/prices_daily |
| 7 | Models and migrations match | `alembic check` → "No new upgrade operations detected" | ✅ 2026-10-31 |
| 8 | Redis key registry with TTL rule | `tests/unit/infrastructure/test_redis_keys.py` | ✅ 2026-10-31 (6 tests) |
| 9 | Fresh clone reproducible from the repo | `git clone` → `make bootstrap` → `make dev` on a clean machine | 🟡 2026-11-01: fresh `git clone` + `.env` from `.env.example` → `make test` (83 + 76) and `make e2e` (22) pass. Still to do by you: `make bootstrap` → `make dev` on a machine with an empty Docker cache |

---

### D1.2 – Domain core
**Outcome:** the business rules are correct, framework-free and proven by unit tests.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `Money` and `Percentage` are immutable `Decimal` value objects (no floats) | Unit tests | ✅ 2026-11-01: `domain/shared/money.py` (`Money`, `Percentage`; rejects floats, NaN, mixed currencies); `test_money.py` (9 tests) |
| 2 | `HoldingCategory` covers 50D, 100D, 200D, 300D, 1Y, 2Y, 3Y and converts calendar days to trading days | Unit tests with the trading calendar | ✅ 2026-10-31: `test_calendar_and_categories.py` |
| 3 | `TradingCalendar` skips weekends and NSE holidays | Unit tests | ✅ 2026-10-31: `test_calendar_and_categories.py` |
| 4 | `TradePlan`: prediction locked at start; can't close twice; exit date not before start | Unit tests for each rule | ✅ 2026-10-31: `test_trade_plan.py` |
| 5 | Outcome rule: equal within tolerance = SUCCESS, above = PARTIAL (tuning required), below = FAILURE; default ±0.5 pp; tolerance saved per plan | Table-driven unit tests incl. edge values (9.5, 10.5, 10.6, 9.4 for a 10% prediction) | ✅ 2026-10-31: table-driven test incl. 9.5 / 10.5 / 10.6 / 9.4 |
| 6 | Domain imports no frameworks | import-linter contract passes | ✅ 2026-10-31: import-linter 'Domain is framework-free' KEPT |
| 7 | Coverage of `domain/` ≥ 90% | Coverage report | ✅ 2026-10-31: 97% |

---

### D1.3 – Synthetic data + mock provider
**Outcome:** 5 years of realistic, repeatable NIFTY 50 data is in the database, loaded through the same ports a real provider will use.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `MarketDataProvider` and `FundamentalsProvider` ports defined in `application/ports/` | Code review | ✅ 2026-11-01: `application/ports/fundamentals.py` (`FundamentalsProvider`) |
| 2 | Mock plugins registered in the provider registry; selectable as primary | `GET /api/admin/providers` lists `mock` | ✅ 2026-10-31: `GET /api/admin/providers` lists `mock`; test returns OK |
| 3 | Generator: 50 symbols with sectors, 5 years of trading days, bull/bear/sideways regimes, OHLC + volume, splits/bonuses, quarterly fundamentals | Generator unit tests (ranges, OHLC consistency high ≥ open/close ≥ low) | ✅ 2026-11-01: quarterly fundamentals added (`mock/fundamentals.py`; announced 30–45 days after quarter end, point-in-time); `make seed` → 956 quarters |
| 4 | Same seed → identical data | Test compares two runs | ✅ 2026-10-31: `test_mock_provider.py` |
| 5 | `make seed` loads everything; running it twice creates no duplicates | Row counts identical after 2nd run | ✅ 2026-10-31: 50 stocks, 64,300 candles; identical after a 2nd run |
| 6 | Every record has `source_provider = "mock"` | SQL check | ✅ 2026-10-31: 0 non-mock rows |

---

### D1.4 – Baseline predictions
**Outcome:** every stock has an honest, statistics-only prediction for every holding category.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `make predict` produces 50 stocks × 7 categories = 350 predictions | SQL count | ✅ 2026-10-31: 350 predictions, 1 model version, idempotent |
| 2 | Each prediction has p10 ≤ p50 ≤ p90 and target probabilities for 5 … 50% (non-increasing as the target rises) | Unit + property tests | ✅ 2026-10-31: DB check constraint + `test_baseline_prediction.py` |
| 3 | No future data: only returns that ended before the prediction date are used | Data-leakage test | ✅ 2026-10-31: `test_no_future_data_is_used` |
| 4 | Stored with `model_version = baseline-empirical-v1` | SQL check | ✅ 2026-10-31 |
| 5 | Pure statistics, no LLM involvement | Code review | ✅ 2026-10-31: `domain/prediction/baseline.py` |

---

### D1.5 – API
**Outcome:** the POC features are available through documented, tested REST endpoints.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `GET /api/stocks?query=` (search) and `GET /api/stocks/{symbol}` | e2e tests | ✅ 2026-10-31: `test_stocks_api.py` |
| 2 | `GET /api/stocks/{symbol}/prices?from=&to=` | e2e tests | ✅ 2026-10-31: `test_stocks_api.py` |
| 3 | `GET /api/predictions/{symbol}` returns all 7 categories with range + probabilities | e2e tests | ✅ 2026-10-31: path is `/api/stocks/{symbol}/predictions`; `test_stocks_api.py` |
| 4 | `POST /api/trade-plans`, `GET /api/trade-plans`, `GET /api/trade-plans/{id}`, `POST /api/trade-plans/{id}/close` (outcome calculated server-side) | e2e tests incl. error cases (close twice → 409) | ✅ 2026-10-31: `test_trade_plans_api.py` (201, 404, 409, 422) |
| 5 | `GET /api/admin/providers`, `POST /api/admin/providers/{id}/test` | e2e tests | ✅ 2026-10-31: `test_admin_providers_api.py` |
| 6 | Every endpoint documented with summary + examples | `http://localhost:8000/docs` | ✅ 2026-11-01: response examples on every model; `test_openapi_docs.py` enforces summaries + examples. New: `GET /api/stocks/{symbol}/fundamentals` |
| 7 | TypeScript client regenerated | `make api-client`; frontend type-check passes | ✅ 2026-10-31: 10 endpoints typed; `tsc` passes |

---

### D1.6 – Frontend
**Outcome:** the whole POC flow works in the browser and is clearly labelled as synthetic.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Layout: sidebar navigation (Stocks, Journal, Admin › Providers), top bar with **SYNTHETIC DATA** badge | Screenshot | ✅ 2026-11-01: redesigned shell (Phase 1b); `make ui-shots` |
| 2 | Stock search (combobox) finds any of the 50 symbols | Component test + screenshot | ✅ 2026-11-01: ⌘K command palette; `make e2e` `command-palette.e2e.mjs` |
| 3 | Stock page: candlestick chart (Lightweight Charts) + prediction card per category in the headline format `+9% (−6…+24%) · 41% chance of +20%`; CAGR only for 1Y+ | Screenshot | ✅ 2026-11-01: `stock-desktop-light.png` (Phase 1b) |
| 4 | Journal: start a plan (stock, start date, category, entry price prefilled, target, stop, tolerance), list plans, close a plan → outcome shown | Playwright e2e | ✅ 2026-11-01: `make e2e` `journal.e2e.mjs` (start, preview Success/Partial/Failure, close, cancel) |
| 5 | Admin › Providers shows the mock provider and a working "Test connection" | Screenshot | ✅ 2026-11-01: `providers-desktop-light.png` |
| 6 | Money formatted in ₹ (lakh/crore), dates in IST | Unit tests for formatters | ✅ 2026-10-31: `format-number.test.ts`, `format-date.test.ts` |

---

### D1.7 – Wrap-up
**Outcome:** anyone can run and understand the POC, and it is merged into `develop`.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Demo script: from `make dev` to a closed plan in ≤ 10 steps | `docs/deliverables/phase-01-demo.md` | ✅ 2026-10-31: [phase-01-demo.md](phase-01-demo.md) |
| 2 | Docs updated (decisions, schema, endpoints) and CHANGELOG entry | PR diff | ✅ 2026-10-31 |
| 3 | Definition of Done met for every change | Checklist in the PR | ✅ 2026-11-01: lint, tests (74 backend + 20 frontend), 12 browser tests, pre-commit |
| 4 | PR `feature/phase1-foundation` → `develop` merged | PR link | ✅ PR #3 (Phase 1), PR #4 (UI); completion PR pending |

---

## Phase exit criteria
- [ ] D1.0 – D1.7 all ✅
- [x] `make lint` and `make test` pass in containers (2026-11-01; plus `make e2e` 22/22)
- [ ] Demo walked through end to end on a fresh `make dev`
- [x] Docs and Open Questions updated
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-10-31 | Phase 1 defined as a POC on synthetic data | Prove the flow before paying for APIs (Q56) |
| 2026-10-31 | POC built end to end on synthetic data (backend + frontend); open items: pre-commit, DB integration tests, FundamentalsProvider + fundamentals, Playwright, screenshots | Shown to the user for review |
| 2026-11-01 | Phase 1 finish: `Money`/`Percentage`, Button render test, fresh-clone run, visual regression | Close remaining criteria |
| 2026-11-01 | POC completion: fundamentals, DB integration tests, pre-commit, Playwright e2e (found + fixed ⌘K crash and a missing focus ring), API examples | Close open items |
| 2026-10-31 | D1.1 extended: Alembic commands, drift check, Redis key registry, reproducible bootstrap | Database control + clone-and-run setup |
