# Model evaluation (walk-forward)

_Synthetic data (mock provider): not evidence of real-world skill._

Pinball loss: lower is better (average over p10/p50/p90). Coverage: share of outcomes
inside the 80% range (target 75-85%). ECE: calibration error of the probabilities in
percentage points (≤ 5). A model becomes ACTIVE only when every gate passes (Q51).

| Category | Samples | Folds | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction | Gates | Result |
|---|---|---|---|---|---|---|---|---|
| 50D | 10550 | 3 | 3.0349 / 2.9669 / 2.9813 | 0.8721 | 4.79 | 0.5885 | failed: beats_baselines, range_coverage, stability | kept current / baseline |
| 100D | 10200 | 3 | 4.2865 / 4.0149 / 4.0385 | 0.8818 | 10.57 | 0.5599 | failed: beats_baselines, calibration, range_coverage, stability | kept current / baseline |
| 200D | 9500 | 3 | 5.8182 / 5.3251 / 5.2643 | 0.8622 | 13.8 | 0.5421 | failed: beats_baselines, calibration, range_coverage, stability | kept current / baseline |
| 300D | 8800 | 2 | 6.7486 / 5.8278 / 5.6587 | 0.8523 | 6.15 | 0.4534 | failed: beats_baselines, calibration, range_coverage, stability | kept current / baseline |
| 1Y | 8350 | 1 | 7.9604 / 7.5582 / 7.0834 | 0.805 | 11.66 | 0.5425 | failed: beats_baselines, calibration, stability | kept current / baseline |
| 2Y | 5850 | 0 | — / — / — | — | — | — | failed: enough_data | not trained (too little data) |
| 3Y | 3350 | 0 | — / — / — | — | — | — | failed: enough_data | not trained (too little data) |

## Folds

### 50D

| Test period | Samples | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction |
|---|---|---|---|---|---|
| 2024-05-06 … 2025-02-06 | 2000 | 3.2682 / 3.3858 / 3.5388 | 0.832 | 6.06 | 0.624 |
| 2025-02-13 … 2025-11-18 | 2000 | 3.0677 / 2.715 / 2.677 | 0.93 | 2.1 | 0.53 |
| 2025-11-25 … 2026-09-11 | 2100 | 2.769 / 2.7999 / 2.7283 | 0.8543 | 6.19 | 0.6114 |

### 100D

| Test period | Samples | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction |
|---|---|---|---|---|---|
| 2024-07-08 … 2025-03-06 | 1750 | 4.2873 / 4.0872 / 4.3735 | 0.8851 | 17.23 | 0.5331 |
| 2025-03-13 … 2025-11-11 | 1750 | 4.5662 / 3.7426 / 3.7232 | 0.9069 | 2.38 | 0.5 |
| 2025-11-18 … 2026-07-24 | 1800 | 4.006 / 4.2149 / 4.0189 | 0.8533 | 12.09 | 0.6467 |

### 200D

| Test period | Samples | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction |
|---|---|---|---|---|---|
| 2024-11-06 … 2025-04-17 | 1200 | 5.4645 / 5.1174 / 5.2494 | 0.875 | 22.34 | 0.5067 |
| 2025-04-24 … 2025-10-07 | 1200 | 5.6173 / 4.369 / 4.421 | 0.825 | 3.39 | 0.4092 |
| 2025-10-14 … 2026-04-16 | 1350 | 6.3726 / 6.489 / 6.1224 | 0.8867 | 15.68 | 0.7104 |

### 300D

| Test period | Samples | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction |
|---|---|---|---|---|---|
| 2025-06-06 … 2025-09-08 | 700 | 5.8325 / 4.8014 / 4.8138 | 0.8857 | 5.38 | 0.3986 |
| 2025-09-15 … 2026-01-07 | 850 | 7.6647 / 6.8542 / 6.5037 | 0.8188 | 6.92 | 0.5082 |

### 1Y

| Test period | Samples | Pinball (model / universe / momentum) | Coverage | ECE pp | Direction |
|---|---|---|---|---|---|
| 2025-09-15 … 2025-11-04 | 400 | 7.9604 / 7.5582 / 7.0834 | 0.805 | 11.66 | 0.5425 |
