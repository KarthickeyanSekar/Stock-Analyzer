<!-- nav -->[← Previous](02-short-term-analyzer.md) · [🏠 Index](README.md) · [Next →](04-data-sources.md)

# 03 – Long-Term Analyzer 🔵

**Status:** ✅ Built first. **Horizon:** 50D · 100D · 200D · 300D · 1Y · 2Y · 3Y · **Refresh:** nightly predictions from end-of-day prices; fundamentals after results

**Approach: both** rule-based scoring and ML forecasting.
- **Rule-based** answers *"Is this a good stock at a fair price?"*
- **ML forecast** answers *"If I hold for N days, what % can I expect, and how likely is it?"*

## Features / inputs
The full checklist of data points, formulas and thresholds is in [21 – Stock Analysis Data Points 🧮](21-stock-analysis-datapoints.md). Summary:

### Fundamentals
- Revenue and EPS growth, profit margins, ROE, ROCE, debt/equity, free cash flow
### Valuation
- P/E, P/B, PEG, EV/EBITDA compared with sector peers and the stock's own history
### Quality
- Earnings consistency, dividend history, promoter/insider holding
### Macro
- Interest rates, inflation, sector outlook
### Long price trend
- 200-day moving average, 1/3/5-year returns

## Methods / models
- **Fair value:** DCF (Discounted Cash Flow), Graham number
- **Scoring:** Piotroski F-Score, Altman Z-Score, custom quality score (0–10)
- **Return forecast:** quantile models per holding category → p10 / p50 / p90 return and probability of hitting a target ([18](18-methods-accuracy-references.md))
- **Scenarios:** bull / base / bear cases

## Holding categories
**50D · 100D · 200D · 300D · 1Y · 2Y · 3Y** (5Y optional), each with its own model. Filter by category and target % in the [16 – Holding-Period Screener 🔎](16-holding-period-screener.md).

## ML holding-period forecast
- Separate models for each holding category (50D … 3Y)
- Inputs: the rule-based scores **plus** trend, momentum, volatility, sector and NIFTY context
- Outputs: expected return %, probability of hitting a target % before the stop-loss, expected days to target
- Models: LightGBM / XGBoost (quantile regression for ranges), survival analysis for time to target
- Example output: *"Hold ~50 days → +20% target, 41% probability, median expected +9%"*

## How the two combine
| Rule-based score | ML forecast | Verdict |
|---|---|---|
| High | Strong | ✅ Buy, with an entry/exit plan |
| High | Weak | ⏳ Watchlist: good company, wait for the entry trigger |
| Low | Strong | ⚠️ Trade only, with a strict stop |
| Low | Weak | ❌ Avoid |

Entry and exit rules are in [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md).

## Output example
```
INFY (NSE) – Long-term view (3Y category)
Fair value:     ₹1,920  (current ₹1,650 → 16% upside)
Expected CAGR:  11–14% per year
Quality score:  8/10
Valuation:      Fairly priced vs sector
Risk level:     Low
Verdict:        Accumulate
```

## Evaluation
- Backtest the score: "top 20 by score, rebalanced yearly" vs the index
- Compare against the benchmark (NIFTY 50 / S&P 500)

## Related
- [04 – Data Sources](04-data-sources.md)
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [09 – Roadmap](09-roadmap.md)
- [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](02-short-term-analyzer.md) · [🏠 Index](README.md) · [Next →](04-data-sources.md)
