<!-- nav -->[← Previous](01-overview.md) · [🏠 Index](README.md) · [Next →](03-long-term-analyzer.md)

# 02 – Short-Term Analyzer 🟢

> ⏭️ **Later phase (Phase 7).** Long-term is built first. This doc is kept as the plan for when short-term starts.

**Horizon:** 1 day – 2 weeks (swing trading, India NSE/BSE) · **Data:** end-of-day + hourly snapshots (no intraday trading) · **Refresh:** daily

## Features / inputs
### Technical indicators
- RSI, MACD, EMA (9/21/50), SMA, Bollinger Bands, ATR, OBV (daily candles; VWAP is left out because there is no intraday data)
### Price & volume
- Returns over 1/5/10 days, lagged prices, volatility
- Volume spikes and volume trend
### Sentiment (optional)
- News headlines scored with FinBERT (a small ML model, not an LLM), only if a news provider is added
### Market context
- NIFTY 50 trend, sector index strength, India VIX
### Event flags
- Upcoming earnings, dividends, splits, holidays

## Models
- **Classification:** Up / Down / Flat with a probability (Logistic Regression, XGBoost, LightGBM)
- **Regression:** expected % change over N days
- **Sequence models (optional):** LSTM / GRU
- **Volatility:** GARCH for the expected price range

## Output example
```
TCS (NSE) – Next 5 days
Expected move:       +2.1%  (range −1.5% to +4.8%)
Probability up:      64%
Signal:              Buy / Hold / Avoid
Suggested stop-loss: −2.5%   Target: +4%
Confidence:          Medium
```

## Entry & exit
Entry triggers, stop-loss, target and time stop (max 2 weeks) are defined in [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md#1-entry-signals-when-to-start).

## Evaluation
- Directional accuracy, precision on "Buy" signals
- Backtest with transaction costs: win rate, Sharpe ratio, max drawdown
- Compare against "tomorrow = today" and moving-average baselines

## Related
- [04 – Data Sources](04-data-sources.md)
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [10 – AI / LLM Integration (OpenAI or Local Models)](10-ai-llm-integration.md)
- [11 – Live Cloud Data (Actual Values)](11-live-cloud-data.md)
- [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](01-overview.md) · [🏠 Index](README.md) · [Next →](03-long-term-analyzer.md)
