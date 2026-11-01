[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-04-screener.md) · [Next phase →](phase-05b-users.md)

# Phase 5 – Validation

**Phase outcome:** The system's usefulness is proven (or disproven) with out-of-sample backtests and the journal's real track record.
**Status:** 🟡 Validation tools built and verified; **verdict pending real data and real journal plans** · **Branch:** `feature/phase5-validation` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D5.1 | Backtests | Purged walk-forward backtests of full plans, net of costs and taxes, vs NIFTY 50 | ✅ Tools built; real-data run pending |
| D5.2 | Calibration review | Calibration and range coverage verified per category | ✅ Tools built; real-data run pending |
| D5.3 | Journal review | Real SUCCESS/PARTIAL/FAILURE rates compared with predictions | 🟡 Report built; needs ≥ 30 real closed plans |
| D5.4 | Go / no-go | A written decision on whether predictions are good enough to rely on | 🟡 Criteria set (Q70); verdict 'not decidable' until real data |

---

### D5.1 – Backtests
**Outcome:** Purged walk-forward backtests of full plans, net of costs and taxes, vs NIFTY 50.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Plan simulator: enter at the close, exit at the target, the −7% stop or the end date (whichever first); gross and net return | Unit tests per exit reason | ✅ 2026-11-01: `domain/validation/backtest.py`; `test_simulate_exits_at_the_first_barrier` |
| 2 | Costs (default 0.25% round trip) and taxes (STCG 20% under a year, LTCG 12.5% from a year; conservative: no exemption, no loss set-off) configurable (doc 12, Q69) | Unit tests | ✅ 2026-11-01: `CostModel` (Q69); `test_costs_and_tax_are_conservative` |
| 3 | Point-in-time strategy: every 40 trading days, per holding period, the top 5 stocks by the predicted chance of the target, using only data known that day | Leakage test | ✅ 2026-11-01: `RunValidation`; leakage test (rewriting prices after a cutoff leaves earlier picks unchanged) |
| 4 | Benchmark over the same windows: NIFTY 50 index (real data) or the equal-weight universe (synthetic data, labelled) | Report | ✅ 2026-11-01: equal-weight universe on synthetic data (labelled); NIFTY 50 index series to add with real data |
| 5 | `make validate` writes `docs/reports/validation.md`: trades, win rate, average gain / loss, expectancy, holding days, net return vs benchmark per holding period | Report + job test | ✅ 2026-11-01: `docs/reports/validation.md` (dev: 510 simulated plans across 5 holding periods) |

---

### D5.2 – Calibration review
**Outcome:** Calibration and range coverage verified per category.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Reliability table per holding period: predicted chance (in 10% buckets) vs what happened, ECE, and 80%-range coverage of the same point-in-time predictions | Report section; unit test | ✅ 2026-11-01: report section; `test_reliability_buckets` |

---

### D5.3 – Journal review
**Outcome:** Real SUCCESS/PARTIAL/FAILURE rates compared with predictions.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Journal section: SUCCESS / PARTIAL / FAILURE counts and rates per holding period vs the predicted chance; flagged 'not enough plans' below 30 closed plans | Report section; unit test | ✅ 2026-11-01: report section (2 closed plans on dev → flagged too few) |

---

### D5.4 – Go / no-go
**Outcome:** A written decision on whether predictions are good enough to rely on.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Go / no-go criteria written down (Q70): net expectancy beats the benchmark, ECE ≤ 5 pp, coverage 75–85%, ≥ 30 closed journal plans | Decision log | ✅ 2026-11-01: Q70 in the decision log |
| 2 | The report states the verdict per holding period from those criteria; on synthetic data it says 'not decidable' | Report | ✅ 2026-11-01: all 5 periods 'not decidable' (synthetic); `test_verdict_rules` |

---

## Result on synthetic data (2026-11-01)
`docs/reports/validation.md`: every holding period is **not decidable** (synthetic data). Useful findings
already: the top-5 picks are **over-confident** (e.g. 50D: predicted 71% chance of +5%, happened 51%),
net expectancy mostly trails the equal-weight benchmark, and calibration error is above 5 pp in every
period. Re-run `make validate` after `make real-data`, and again once the journal has ≥ 30 closed plans
per holding period.

## Phase exit criteria
- [ ] All deliverables ✅
- [x] `make lint` and `make test` pass in containers
- [x] Docs and Open Questions updated (Q69, Q70)
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Tools built; verdict not decidable on synthetic data | Needs real data and plans |
| 2026-11-01 | Phase planned: tools now; the verdict needs real data and real plans | Phase 5 started |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
