[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-02-trade-journal.md) · [Next phase →](phase-04-screener.md)

# Phase 3 – Long-Term Engine

**Phase outcome:** ML predictions per holding category, with calibrated ranges and target probabilities, beat the baseline models.
**Status:** 🟡 Engine built and verified; **outcome not yet met** (synthetic data has no learnable signal, see below) · **Branch:** `feature/phase3-engine` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D3.1 | Data points | The researched data points (doc 21) are computed for every stock and date | ✅ |
| D3.2 | Feature store & labels | Point-in-time features and triple-barrier labels are stored and versioned | ✅ |
| D3.3 | Models per category | LightGBM quantile + target-probability models trained for 50D … 3Y | ✅ |
| D3.4 | Calibration | 80% ranges contain 75–85% of outcomes; calibration error ≤ 5 pp | 🟡 Machinery ✅; target not met on synthetic data |
| D3.5 | Quality gates & registry | Only models that pass the gates become ACTIVE; rollback works | ✅ |

---

### D3.1 – Data points
**Outcome:** The researched data points (doc 21) are computed for every stock and date.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Pure-domain calculators for every doc 21 data point our data supports: trend (price vs 50/200-DMA, golden cross, 52-week distance, momentum 3M/6M/12-1M, relative strength vs universe, volatility, ATR %, max drawdown, beta, volume trend), valuation (P/E, P/B, earnings yield, PEG, Graham number), profitability (ROE, net margin), growth (revenue/EPS YoY, revenue CAGR 3Y), health (D/E) | Unit tests per calculator with hand-checked values | ✅ 2026-11-01: `domain/analysis/datapoints.py` + `features.py`; `test_datapoints.py` |
| 2 | A coverage table in doc 21 marks each data point computed / needs a real provider (e.g., delivery %, promoter pledge, cash flow) | Doc 21 | ✅ 2026-11-01: doc 21 'Implementation coverage' |
| 3 | Fundamentals are used only from their announcement date (point-in-time) | Leakage test | ✅ 2026-11-01: `build_features` rejects later quarters; `test_features_refuse_future_inputs` |

---

### D3.2 – Feature store & labels
**Outcome:** Point-in-time features and triple-barrier labels are stored and versioned.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `features_daily` (stock × date × feature-set version) and `labels_daily` (stock × date × category) tables via migration | Migration round trip + `alembic check` | ✅ 2026-11-01: migration 0005; round trip + `alembic check` clean |
| 2 | Cross-sectional ranks per date (percentile within the universe) for the main features | Unit test | ✅ 2026-11-01: `percentile_ranks` (ties, missing); 8 ranked features |
| 3 | Labels: forward return, triple-barrier outcome (target / stop / time), target-hit flags 5…50% before a −7% stop; empty when the horizon passes the data end | Unit tests | ✅ 2026-11-01: `labels.py`; `test_label_triple_barrier`, `test_label_time_barrier_and_missing_future` |
| 4 | Leakage tests: changing any price after date t never changes features at t; labels at t use only prices after t | Leakage tests | ✅ 2026-11-01: `test_features_ignore_future_prices_and_labels_use_them` (rewrites all prices after a cutoff) |
| 5 | `make features` builds both, idempotent; feature set has a version string | Integration test | ✅ 2026-11-01: dev DB 218 dates, 10,900 vectors, 56,600 labels; idempotent (unit + DB tests) |

---

### D3.3 – Models per category
**Outcome:** LightGBM quantile + target-probability models trained for 50D … 3Y.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Per category: LightGBM quantile models (p10/p50/p90) and one classifier per target with isotonic calibration | Training run log; artifacts in the `models` volume | ✅ 2026-11-01: `infrastructure/ml/lightgbm_trainer.py`; 5 categories trained on dev (2Y/3Y: too little data) |
| 2 | Purged walk-forward evaluation with an embargo equal to the holding period | Unit test of the splitter (no overlap) | ✅ 2026-11-01: `test_walk_forward_folds_are_purged` |
| 3 | Baselines evaluated on the same folds: empirical (current) and momentum-only | Evaluation report | ✅ 2026-11-01: universe + momentum terciles in `docs/reports/model-evaluation.md` |
| 4 | Reproducible: fixed seeds; params, feature-set version, data end date and code version stored on the model version | Registry row | ✅ 2026-11-01: same scores in memory and on dev DB; params incl. `code_version`, `data_end`, `feature_set` on the version |

---

### D3.4 – Calibration
**Outcome:** 80% ranges contain 75–85% of outcomes; calibration error ≤ 5 pp.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Ranges calibrated with split conformal prediction on a held-out fold | Unit test: ~80% coverage on a known distribution | ✅ 2026-11-01: `test_conformal_margin_reaches_the_target_coverage` (77–83% on a known distribution) |
| 2 | Walk-forward report per category: 80% coverage, ECE of target probabilities, pinball loss vs baselines, direction accuracy | `make evaluate` → `docs/reports/phase3-evaluation.md` | ✅ 2026-11-01: `docs/reports/model-evaluation.md` (`make train`) |

---

### D3.5 – Quality gates & registry
**Outcome:** Only models that pass the gates become ACTIVE; rollback works.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Gates (Q51) evaluated per candidate; the result is stored on the model version | Unit tests per gate | ✅ 2026-11-01: `test_gates_pass_and_fail`; report stored in `model_versions.metrics` |
| 2 | Only a candidate that passes every gate becomes ACTIVE (the previous one RETIRED); otherwise the current model stays | Registry test | ✅ 2026-11-01: `test_only_passing_models_activate_and_rollback_restores`; on dev all 7 kept the baseline |
| 3 | `make model-rollback c=<category>` re-activates the previous version | Registry test | ✅ 2026-11-01: unit + DB test (`test_registry_keeps_one_active_model_and_rolls_back`, incl. the DB's one-ACTIVE index) |
| 4 | `make predict` uses the ACTIVE ML model per category and falls back to the baseline; every prediction stores its model version | Integration test | ✅ 2026-11-01: `test_predictions_use_the_active_model_and_fall_back_to_the_baseline`; dev: 0 ML + 350 baseline |

---

## Result on synthetic data (2026-11-01)
The engine works end to end, but **no ML model beat the baselines**, so the gates kept the empirical
baseline ACTIVE for every category (`docs/reports/model-evaluation.md`):
- 50D–1Y: pinball loss worse than both baselines; 80% coverage 0.81–0.88 (target 0.75–0.85); ECE 4.8–13.8 pp.
- 2Y, 3Y: too little history for a single purged walk-forward fold.

This is the expected, honest outcome: the mock provider generates regime-switching random walks and
fundamentals that do not drive returns, so there is nothing for a model to learn. The phase outcome
("beat the baselines", calibration within targets) can only be demonstrated on **real data** from a
managed provider. Re-run `make ml-data` once real data is loaded.

## Phase exit criteria
- [ ] All deliverables ✅
- [x] `make lint` and `make test` pass in containers
- [x] Docs and Open Questions updated (Q50, Q51, Q64; docs 21, 26)
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Engine built; gates kept the baseline on synthetic data | Outcome needs real data |
| 2026-11-01 | Phase planned: detailed criteria; Q50, Q51, Q64 decided | Phase 3 started |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
