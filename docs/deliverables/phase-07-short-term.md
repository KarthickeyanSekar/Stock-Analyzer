[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-06-daily-ops.md) · [Next phase →](phase-08-optional.md)

# Phase 7 – Short-Term

**Phase outcome:** A 1 day – 2 weeks engine is available alongside the long-term one.
**Status:** ✅ Complete, signed off 2026-11-02 · **Branch:** `feature/phase7-short-term` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D7.1 | Short-term models | Signals with ranges and probabilities for 1–10 day holds | ✅ |
| D7.2 | Short-term UI | Short-term tab and combined card | ✅ |

---

### D7.1 – Short-term models
**Outcome:** Signals with ranges and probabilities for 1–10 day holds.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Holding periods 1D, 3D, 5D, 10D in trading sessions (Q75); planned end date = N sessions later | Unit tests; migration updates the category checks | ✅ 2026-11-01: `test_short_holds_count_trading_sessions_and_use_a_tighter_stop`; migration 0008 (round trip + `alembic check`) |
| 2 | Targets +1/+2/+3% and a −3% stop for short holds (Q76) in labels, baseline and journal defaults | Unit tests | ✅ 2026-11-01: labels, baseline and journal use the category stop; `test_short_holds_default_to_a_tight_stop_and_end_in_sessions` |
| 3 | Short-term technicals in feature set fs-v2: RSI 14, MACD histogram, EMA 9/21 gap, Bollinger %B, OBV trend, 1/5/10-day returns, volume spike | Unit tests per indicator; leakage test still passes | ✅ 2026-11-01: `test_short_term.py` (RSI, EMA/MACD, Bollinger, OBV, volume spike); leakage tests pass on fs-v2 |
| 4 | Baseline and ML pipeline produce short-term predictions (range, chance up, target probabilities) with the same gates and registry | `make predict` / `make train` on dev; tests | ✅ 2026-11-01: dev `make features` (99,850 labels) + `make predict` (550 = 50 stocks × 11 periods) |
| 5 | Setup label Favourable / Neutral / Unfavourable from the prediction (Q77) | Unit tests | ✅ 2026-11-01: `domain/prediction/setup.py`; `test_setup_label` |

---

### D7.2 – Short-term UI
**Outcome:** Short-term tab and combined card.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Stock page: Short-term / Long-term tabs over the predictions, with the setup label for short holds | Playwright + visual baseline | ✅ 2026-11-01: `phase7.e2e.mjs`; `stock-*.png` baselines |
| 2 | Combined card: next 5 days and 1 year side by side | Playwright | ✅ 2026-11-01: Outlook card; `phase7.e2e.mjs` |
| 3 | Screener and journal accept short holds (targets +1…+5%, −3% stop by default) | e2e tests | ✅ 2026-11-01: `phase7.e2e.mjs` (5D screen, 5D plan with −3% stop); API test |

---

## Phase exit criteria
- [x] All deliverables ✅
- [x] `make lint` and `make test` pass in containers
- [x] Docs and Open Questions updated
- [x] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| 2026-11-02 | Karthikeyan Sekar (owner) | Signed off ("complete it"). Known limit: synthetic data, so short-term numbers show no real skill until `make real-data`; sentiment / sector / VIX / events need real providers. |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-02 | Built, verified and signed off | Phase 7 delivered |
| 2026-11-01 | Phase planned: detailed criteria; Q75–Q77 decided | Phase 7 started (before Phase 6 at the owner's request) |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
