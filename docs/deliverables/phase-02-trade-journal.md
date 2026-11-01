[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-01-foundation-poc.md) · [Next phase →](phase-03-long-term-engine.md)

# Phase 2 – Trade Journal

**Phase outcome:** Users can track holding plans manually, end to end, with honest calculated outcomes on real or synthetic prices.
**Status:** 🟢 Built and verified, awaiting your sign-off · **Branch:** `feature/phase2-journal` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D2.1 | Journal decisions | Q28 (calendar vs trading days), Q29 (entry price) and Q31 (own target %) are decided and implemented | ✅ |
| D2.2 | Daily plan tracking | Active plans show day N of M, current return and progress to target, updated from hourly/EOD prices | ✅ |
| D2.3 | Stop-loss & time stop | Plans flag target reached, stop-loss crossed and end date reached automatically | ✅ |
| D2.4 | Settings | Paper capital, risk % (default 1%) and tolerance (default ±0.5 pp) are configurable; suggested amount shown | ✅ |
| D2.5 | Track record | Success / partial / failure rates per category and actual vs predicted are shown | ✅ |

---

### D2.1 – Journal decisions
**Outcome:** Q28 (calendar vs trading days), Q29 (entry price) and Q31 (own target %) are decided and implemented.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Q28/Q29/Q31 recorded ✅ in the decision log (+ Q63 settings) | `docs/decisions/open-questions.md` | ✅ 2026-11-01: Q28, Q29, Q31 ✅; new Q63 |
| 2 | Q28: categories are calendar days; an end date on a weekend/holiday moves to the next trading day | Unit tests (`test_calendar_and_categories.py`) | ✅ 2026-11-01: `test_calendar_and_categories.py` |
| 3 | Q29: entry price prefilled with the close on the start date and editable; the API close is stored as `reference_close` next to the entry price, with `entry_source` = CLOSE / MANUAL | Migration 0004; unit + e2e tests | ✅ 2026-11-01: migration 0004; `test_entry_price_is_the_close_unless_typed`; `phase2.e2e.mjs` (MANUAL entry) |
| 4 | Q31: own target % allowed; the locked prediction is stored as `predicted_pct`; the outcome is judged against `predicted_pct` (falls back to the target when there was no prediction); the gap to your own target is reported separately | Unit tests incl. own target ≠ prediction; e2e test | ✅ 2026-11-01: `test_own_target_is_kept_apart_from_the_prediction`, `test_outcome_judged_against_prediction_when_present` |

---

### D2.2 – Daily plan tracking
**Outcome:** Active plans show day N of M, current return and progress to target, updated from hourly/EOD prices.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Plan progress is calculated in the domain from daily candles: day N of M (trading days), last close, return %, progress from stop through entry to target | Unit tests with candle fixtures | ✅ 2026-11-01: `domain/journal/progress.py`; `test_plan_progress.py` |
| 2 | Every plan in the API carries its progress (no maths in the UI) | e2e test; `GET /api/trade-plans` | ✅ 2026-11-01: `progress` on `TradePlanResponse`; `test_active_plans_carry_their_progress` |
| 3 | `make track` stores one `plan_daily_status` row per active plan per trading day; idempotent; uses only candles up to that day (no future data) | Integration test; data-leakage test | ✅ 2026-11-01: `test_tracking_job_is_idempotent_and_point_in_time` (each snapshot = tracking with only past candles); dev run twice → same count |
| 4 | Journal and Home show day N of M, return and the progress bar from the API values | Playwright + visual baseline | ✅ 2026-11-01: `phase2.e2e.mjs`; `journal-*.png` baselines |

---

### D2.3 – Stop-loss & time stop
**Outcome:** Plans flag target reached, stop-loss crossed and end date reached automatically.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Flags per plan: target reached (high ≥ target price), stop-loss crossed (low ≤ stop price), end date reached; with the first date each happened | Table-driven unit tests | ✅ 2026-11-01: parametrised tests incl. 109.95 vs 110 edge; progress stops at the planned end date |
| 2 | Flags shown as labelled badges (icon + text, not colour alone) with a 'Close plan' call to action | Playwright | ✅ 2026-11-01: `phase2.e2e.mjs` (End date reached, Target / Stop badges) |
| 3 | Plans are never closed automatically: the exit stays a manual journal entry (no broker, no orders) | Code review; test that tracking never changes status | ✅ 2026-11-01: `test_tracking_never_closes_a_plan`; integration test checks status stays ACTIVE |

---

### D2.4 – Settings
**Outcome:** Paper capital, risk % (default 1%) and tolerance (default ±0.5 pp) are configurable; suggested amount shown.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | One app-wide settings record: paper capital, risk % (default 1), tolerance (default ±0.5 pp), default stop % (default −7) | Migration 0004; `GET`/`PUT /api/settings/journal` e2e tests incl. validation (422) | ✅ 2026-11-01: `journal_settings` (single-row check); `test_settings_are_defaults_for_new_plans_only` (incl. 422) |
| 2 | Settings page to edit them; the start-plan sheet uses them as defaults | Playwright | ✅ 2026-11-01: `/settings`; `phase2.e2e.mjs` (stop −10 and 2% risk reach the sheet) |
| 3 | Suggested amount and quantity = capital × risk % ÷ |stop %| (capped at capital), calculated server-side by `POST /api/trade-plans/preview` | Unit tests; e2e test | ✅ 2026-11-01: `suggest_position` unit tests; `test_preview_sizes_the_position_from_settings` |
| 4 | Changing settings never changes plans already started (values locked per plan) | Unit/e2e test | ✅ 2026-11-01: `test_settings_are_defaults_for_new_plans_only` |

---

### D2.5 – Track record
**Outcome:** Success / partial / failure rates per category and actual vs predicted are shown.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Summary per category: success / partial / failure counts and rates, average actual − predicted (bias) | e2e test; SQL check | ✅ 2026-11-01: `success_rate` per category in `/api/trade-plans/summary` |
| 2 | Track record tab shows rates per category and actual vs predicted for each closed plan | Playwright + visual baseline | ✅ 2026-11-01: `phase2.e2e.mjs` (track record) |
| 3 | Hit rate against your own targets is shown next to model accuracy | e2e test | ✅ 2026-11-01: `own_target_hit_rate`; 'Your targets reached' in the UI |

---

## Phase exit criteria
- [x] All deliverables ✅
- [x] `make lint` and `make test` pass in containers (2026-11-01: 108 backend incl. 9 DB + 76 frontend; `make e2e` 29/29)
- [x] Docs and Open Questions updated (Q28, Q29, Q31, Q63; doc 15)
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Built: progress + flags, `make track`, settings, preview, track record. Found + fixed: progress after the end date, visual tolerance too loose to catch changed numbers, Vite reloading on test output, phone nav wrapping | Phase 2 delivered |
| 2026-11-01 | Phase planned: detailed criteria; Q28/Q29/Q31/Q63 decided | Phase 2 started |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
