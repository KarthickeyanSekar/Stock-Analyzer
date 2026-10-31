<!-- nav -->[← Previous](04-data-sources.md) · [🏠 Index](README.md) · [Next →](06-app-features.md)

# 05 – Models & Evaluation

**Purpose:** model approaches, evaluation rules and metrics. The long-term methods we actually use (triple-barrier labels, quantile models, conformal ranges, survival analysis) are detailed in [26 – ML Pipeline & Model Operations 🤖](26-ml-pipeline.md) (pipeline) and [18 – Methods, Accuracy & References 📐](18-methods-accuracy-references.md).

## Approaches (simple → advanced)
1. **Baselines (always first):** "tomorrow = today", moving average
2. **Statistical:** ARIMA/SARIMA, Prophet, GARCH
3. **Machine learning:** Linear/Ridge, Random Forest, XGBoost, LightGBM
4. **Deep learning (optional, later):** LSTM, GRU, Temporal Fusion Transformer, only if they beat the simpler models
5. **Classification framing:** up/down/flat with a probability
6. **Rule-based (long-term):** DCF, F-Score, Z-Score, custom scoring

## Evaluation rules
- **Purged walk-forward / time-series split.** Never shuffle randomly, because that leaks future data; leave a gap equal to the holding period between training and test data.
- Every model must beat its baseline.
- Report confidence intervals and ranges.

## Metrics
| Metric | Purpose |
|---|---|
| MAE, RMSE, MAPE | Size of price/return errors |
| Directional accuracy | % of up/down calls that were right |
| Precision / recall | Quality of Buy signals |
| Sharpe ratio, max drawdown, win rate | Backtest performance |
| Return vs benchmark | Long-term score validation |
| Interval coverage | Does the 80% range contain ~80% of actual results? |
| Calibration | Do "40% probability" calls succeed ~40% of the time? |
| Journal success rate | Real results of tracked plans ([15](15-trade-journal.md)) |

## Backtesting tools
- `backtrader`, `vectorbt`; always include transaction costs and slippage

## Reality check
Realistic accuracy targets are in [18](18-methods-accuracy-references.md#accuracy-what-to-expect). Short-term prices are very noisy and close to unpredictable. Plan for modest accuracy
(directional accuracy just above 50% can still be useful) and say so clearly in the UI.

## Related
- [02 – Short-Term Analyzer 🟢](02-short-term-analyzer.md)
- [03 – Long-Term Analyzer 🔵](03-long-term-analyzer.md)
- [10 – AI / LLM Integration (OpenAI or Local Models)](10-ai-llm-integration.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](04-data-sources.md) · [🏠 Index](README.md) · [Next →](06-app-features.md)
