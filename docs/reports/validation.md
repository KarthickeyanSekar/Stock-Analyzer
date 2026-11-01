# Validation (Phase 5)

_Data 2021-11-02 … 2026-10-30 · **synthetic** (mock provider): not evidence of real-world skill._

Strategy: every 40 trading days, per holding period, start plans in the top 5 stocks by the predicted chance of the target, using only data known that day (the live empirical predictor). Exit at the target, the -7% stop or the end date. Net of 0.25% costs and tax (STCG 20.0%, LTCG 12.5%; no exemption or loss set-off). Benchmark: equal-weight universe, same windows, same costs and tax.

## Verdict (Q70)

| Holding | Target | Verdict | Why |
|---|---|---|---|
| 50D | +5% | **not decidable** | synthetic data; net expectancy does not beat the benchmark; calibration error above 5 pp; fewer than 30 closed journal plans |
| 100D | +10% | **not decidable** | synthetic data; net expectancy does not beat the benchmark; calibration error above 5 pp; 80% range coverage outside 75-85%; fewer than 30 closed journal plans |
| 200D | +10% | **not decidable** | synthetic data; calibration error above 5 pp; 80% range coverage outside 75-85%; fewer than 30 closed journal plans |
| 300D | +15% | **not decidable** | synthetic data; net expectancy does not beat the benchmark; calibration error above 5 pp; 80% range coverage outside 75-85%; fewer than 30 closed journal plans |
| 1Y | +20% | **not decidable** | synthetic data; net expectancy does not beat the benchmark; calibration error above 5 pp; 80% range coverage outside 75-85%; fewer than 30 closed journal plans |

## Backtest

| Holding | Trades | Win rate | Avg gain | Avg loss | Expectancy (net) | Benchmark | Avg days | Target hit | Predicted chance |
|---|---|---|---|---|---|---|---|---|---|
| 50D | 125 | 55% | +4.47% | -7.90% | -1.07% | -0.33% | 12 | 51% | 71% |
| 100D | 120 | 48% | +8.34% | -8.33% | -0.27% | +0.31% | 24 | 45% | 62% |
| 200D | 105 | 51% | +8.66% | -8.51% | +0.32% | -0.38% | 27 | 51% | 66% |
| 300D | 85 | 22% | +12.70% | -8.43% | -3.70% | -1.78% | 40 | 22% | 62% |
| 1Y | 75 | 25% | +15.68% | -8.37% | -2.27% | -1.82% | 47 | 24% | 59% |

## Calibration

### 50D · chance of +5%

ECE 5.5 pp (≤ 5) · 80% range coverage 82% (75-85%)

| Predicted | Samples | Mean predicted | Happened |
|---|---|---|---|
| 20-30% | 14 | 27% | 50% |
| 30-40% | 25 | 34% | 36% |
| 40-50% | 76 | 46% | 49% |
| 50-60% | 544 | 56% | 56% |
| 60-70% | 506 | 64% | 56% |
| 70-80% | 84 | 73% | 52% |
| 80-90% | 1 | 86% | 0% |

### 100D · chance of +10%

ECE 7.6 pp (≤ 5) · 80% range coverage 87% (75-85%)

| Predicted | Samples | Mean predicted | Happened |
|---|---|---|---|
| 0-10% | 3 | 9% | 33% |
| 10-20% | 30 | 15% | 23% |
| 20-30% | 23 | 26% | 52% |
| 30-40% | 167 | 36% | 44% |
| 40-50% | 495 | 45% | 47% |
| 50-60% | 364 | 55% | 43% |
| 60-70% | 115 | 63% | 46% |
| 70-80% | 3 | 74% | 0% |

### 200D · chance of +10%

ECE 8.9 pp (≤ 5) · 80% range coverage 87% (75-85%)

| Predicted | Samples | Mean predicted | Happened |
|---|---|---|---|
| 10-20% | 7 | 16% | 71% |
| 20-30% | 18 | 26% | 67% |
| 30-40% | 94 | 36% | 50% |
| 40-50% | 300 | 45% | 43% |
| 50-60% | 427 | 54% | 46% |
| 60-70% | 155 | 63% | 54% |
| 70-80% | 37 | 73% | 49% |
| 80-90% | 12 | 81% | 33% |

### 300D · chance of +15%

ECE 16.0 pp (≤ 5) · 80% range coverage 74% (75-85%)

| Predicted | Samples | Mean predicted | Happened |
|---|---|---|---|
| 0-10% | 6 | 5% | 83% |
| 10-20% | 16 | 16% | 56% |
| 20-30% | 37 | 25% | 41% |
| 30-40% | 208 | 36% | 35% |
| 40-50% | 284 | 45% | 32% |
| 50-60% | 220 | 54% | 32% |
| 60-70% | 58 | 63% | 28% |
| 70-80% | 21 | 74% | 29% |

### 1Y · chance of +20%

ECE 15.4 pp (≤ 5) · 80% range coverage 64% (75-85%)

| Predicted | Samples | Mean predicted | Happened |
|---|---|---|---|
| 0-10% | 22 | 4% | 41% |
| 10-20% | 23 | 15% | 35% |
| 20-30% | 89 | 26% | 27% |
| 30-40% | 212 | 35% | 28% |
| 40-50% | 218 | 45% | 28% |
| 50-60% | 139 | 54% | 33% |
| 60-70% | 39 | 63% | 18% |
| 70-80% | 8 | 74% | 0% |

## Journal

Real plans you closed. Below 30 closed plans per holding period the numbers are too few to judge.

| Holding | Closed | Success | Partial | Failure | Exited early |
|---|---|---|---|---|---|
| 50D | 1 | 0 | 1 | 0 | 0 |
| 100D | 0 | 0 | 0 | 0 | 0 |
| 200D | 0 | 0 | 0 | 0 | 0 |
| 300D | 0 | 0 | 0 | 0 | 0 |
| 1Y | 2 | 1 | 0 | 1 | 0 |
