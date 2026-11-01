[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-03-long-term-engine.md) · [Next phase →](phase-05-validation.md)

# Phase 4 – Holding-Period Screener

**Phase outcome:** A user can ask 'N days, X% → which stocks?' and get ranked results with ranges and probabilities in seconds.
**Status:** ✅ Complete, signed off 2026-11-01 · **Branch:** `feature/phase4-screener` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D4.1 | Screener query | Filter by category, target % (range), min probability, max stop, quality, sector | ✅ |
| D4.2 | Stock horizon view | For one stock, all categories side by side with the best risk-adjusted one marked | ✅ |
| D4.3 | Historical analogs | Similar past setups found via pgvector with their outcomes | ✅ |
| D4.4 | Performance | Screener responds in < 2 s for all NSE stocks | ✅ |

---

### D4.1 – Screener query
**Outcome:** Filter by category, target % (range), min probability, max stop, quality, sector.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `GET /api/screener` filters the latest prediction per stock by category, target % (single or range), minimum probability of the target, worst likely return (Q66), minimum quality score (Q67) and sector | e2e tests per filter | ✅ 2026-11-01: `test_screener_api.py` (each filter narrows; 422 on bad input) |
| 2 | Ranked by probability of the target, then median; each row shows median, range, chance up, probability, quality and the model that made it | e2e test | ✅ 2026-11-01: `test_results_are_ranked_by_the_target_probability` |
| 3 | Quality score 0–10 is pure domain maths with unit tests | Unit tests | ✅ 2026-11-01: `domain/analysis/quality.py`; `test_quality_score_bands_and_missing_values` |
| 4 | Screener page: filter bar, ranked table (cards on phones), empty state that suggests relaxing a filter, link to the stock | Playwright + visual baseline | ✅ 2026-11-01: `screener.e2e.mjs`; `screener-*.png` baselines |

---

### D4.2 – Stock horizon view
**Outcome:** For one stock, all categories side by side with the best risk-adjusted one marked.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Each stock's predictions mark the best risk-adjusted category (Q68) in the API | Unit + e2e test | ✅ 2026-11-01: `best_category` (Q68); `test_best_category_is_median_per_unit_of_downside`, API test |
| 2 | Stock page highlights it in the predictions table (label, not colour only) | Playwright + visual baseline | ✅ 2026-11-01: 'Best' label with an icon; `stock-*.png` baselines |

---

### D4.3 – Historical analogs
**Outcome:** Similar past setups found via pgvector with their outcomes.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Feature vectors stored as pgvector embeddings (ranked features, normalised) with an index | Migration round trip | ✅ 2026-11-01: migration 0006 (HNSW, cosine); round trip with 10,900 rows + `alembic check` |
| 2 | `GET /api/stocks/{symbol}/analogs?category=` returns the k most similar past setups of any stock that ended before today, with their outcomes and a summary (median, hit rate) | DB integration test; leakage test (no analog after the query date − horizon) | ✅ 2026-11-01: `test_analogs_only_use_finished_setups`; DB test `test_nearest_setups_use_pgvector_and_respect_the_cutoff` |
| 3 | Stock page shows the analog summary and the closest cases | Playwright | ✅ 2026-11-01: `screener.e2e.mjs` (similar past setups) |

---

### D4.4 – Performance
**Outcome:** Screener responds in < 2 s for all NSE stocks.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Screener query < 2 s with 2,000 synthetic stocks × 7 categories in the database | Benchmark test in the DB integration suite | ✅ 2026-11-01: `test_screener_answers_2000_stocks_in_under_two_seconds` (2,000 stocks × 7 periods × 2 dates) |
| 2 | Supporting indexes on predictions (category, as_of) and the latest-per-stock lookup | Migration; `EXPLAIN` in the benchmark | ✅ 2026-11-01: `ix_predictions_category_stock_as_of` (migration 0006) |

---

## Phase exit criteria
- [x] All deliverables ✅
- [x] `make lint` and `make test` pass in containers
- [x] Docs and Open Questions updated
- [x] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| 2026-11-01 | Karthikeyan Sekar (owner) | Signed off per standing instruction (sign off unless there are concerns). Note: rankings run on synthetic data until `make real-data`; speed proven with 2,000 synthetic stocks. |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Built and verified; signed off | Phase 4 delivered |
| 2026-11-01 | Phase planned: detailed criteria; Q66–Q68 decided | Phase 4 started |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
