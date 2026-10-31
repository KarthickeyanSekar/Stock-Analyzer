<!-- nav -->[← Previous](17-database-backend.md) · [🏠 Index](README.md) · [Next →](19-auth-multi-user.md)

# 18 – Methods, Accuracy & References 📐

**Purpose:** the industry-standard mathematical and business logic to build on, realistic accuracy expectations,
and existing open-source projects to learn from instead of reinventing them.

## Industry-standard methods we will use
| Method | What it does here | Reference |
|---|---|---|
| **Triple-barrier labeling** | Labels each past setup by which comes first: target % (upper barrier), stop-loss (lower) or holding days (time barrier). This is **exactly our plan model** | Marcos López de Prado, *Advances in Financial Machine Learning* |
| **Meta-labeling** | A second model decides whether to *act* on a signal; improves precision | López de Prado |
| **Purged walk-forward validation** | Time-ordered testing with a gap (embargo), so overlapping holding periods don't leak into tests | López de Prado |
| **Quantile regression** (LightGBM / XGBoost) | Predicts p10 / p50 / p90 returns for each holding category | Standard ML |
| **Conformal prediction** | Calibrates the ranges so an 80% range really contains about 80% of outcomes | `MAPIE` library |
| **Survival analysis** | Expected days until the target is reached | `lifelines` library |
| **Factor investing** | Momentum (12-1 month), quality, value, low volatility; well documented for long horizons | Fama-French, AQR research |
| **Fundamental scores** | Piotroski F-Score, Altman Z-Score, Graham number, DCF | Classic value investing |
| **Historical analogs** (kNN) | Similar past setups via pgvector | See [17 – Database & Backend Design 🗄️](17-database-backend.md) |

How these methods run as a pipeline (features, training, registry, nightly predictions, monitoring): [26 – ML Pipeline & Model Operations 🤖](26-ml-pipeline.md).

## Accuracy: what to expect
| Measure | Realistic | Note |
|---|---|---|
| Up/down direction over 50 days | 55–60% | Long horizons are a bit easier than daily ones |
| "Reaches +20% in 50 days" calls | Depends on the threshold; the calibration matters more than the hit rate | A 40%-probability call *should* fail 60% of the time |
| 80% range contains the actual result | ~80% | **Achievable and checkable** |
| Data correctness vs the exchange | **99.9%+** | Achievable with API data + daily checks |
| 99% accuracy on price direction | ❌ Not achievable | Results this high in a backtest almost always mean data leakage |

**How to read "99%" for this project:** aim for 99%+ correct data and reliable, calibrated ranges, not 99% correct predictions.
The trade journal ([15](15-trade-journal.md)) measures the real success rate over time.

## Open-source projects to study (GitHub)
I'm not aware of an open-source project that does exactly this (NSE + holding-period screener + manual plan journal),
but most of the parts exist:
| Project | Useful for |
|---|---|
| **Microsoft Qlib** | Quant research platform: factor models, ML pipelines, backtesting |
| **OpenBB** | Financial data terminal; data-integration patterns |
| **vectorbt** | Fast backtesting of entry/exit rules |
| **backtrader** / **zipline-reloaded** | Event-driven backtesting |
| **empyrical** / **pyfolio** | Performance and risk metrics (Sharpe, drawdown) |
| **MAPIE** | Conformal prediction intervals |
| **lifelines** | Survival analysis (time to target) |
| **FinRL** | Reinforcement learning for trading (advanced, later) |

Check each project's license and maintenance status before depending on it.

## Business logic principles
- **Discipline over greed:** one plan, one target, one exit; re-plan instead of extending ([15](15-trade-journal.md))
- **Risk first:** every plan has a stop-loss and a maximum position size
- **Net returns:** costs and STCG/LTCG tax are included when comparing categories
- **Benchmark:** every result is compared with NIFTY 50 over the same period

## Related
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [16 – Holding-Period Screener 🔎](16-holding-period-screener.md)
- [15 – Trade Journal (Manual Tracking) 📒](15-trade-journal.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](17-database-backend.md) · [🏠 Index](README.md) · [Next →](19-auth-multi-user.md)
