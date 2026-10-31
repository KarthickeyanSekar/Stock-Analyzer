<!-- nav -->[← Previous](00-how-to-plan.md) · [🏠 Index](README.md) · [Next →](02-short-term-analyzer.md)

# 01 – Overview & Goals

## Target market
🇮🇳 **India: NSE / BSE**, prices in ₹, market hours 09:15–15:30 IST. Starting universe: **NIFTY 50**, later expanding to **all NSE stocks**.

### Later: world markets 🌍
India first; other markets (e.g., US, UK, Europe) later. To avoid rework, the design is **market-agnostic from day one**:
- Every stock belongs to a **market** with its own exchange code, **currency**, **timezone**, trading hours and **holiday calendar**
- Schedules (hourly snapshots, EOD jobs) run **per market** in its local time
- Money values store their currency; portfolio totals convert to a base currency (₹ by default)
- Tax and cost rules (STT, STCG/LTCG) are **per-market plugins**; India is the first
- Data providers are chosen per market in the admin UI ([22](22-provider-configuration-ui.md))

## Vision
An application that analyzes stocks and predicts **how much a stock may return over a chosen holding period**,
showing results as **percentages with ranges and probabilities** (e.g., "hold 50 days → +20% target, 41% probability").
Built with a **Python (FastAPI) backend** and a **React frontend**, running in Docker.

## Users
A pet project for **personal use and other users**, who sign up with **OAuth (Google / Microsoft) and a shared invite code** ([19](19-auth-multi-user.md)).

## Two analysis modes
| Aspect | 🟢 Short-Term (Swing trading) · ⏭️ **later** | 🔵 Long-Term (Positional / Investing) · ✅ **first** |
|---|---|---|
| Question | "Will it go up in the next days/weeks?" | "Hold for how long, for what %?" (e.g., 50 days → +20%) |
| Horizon | **1 day – 2 weeks** | **50D · 100D · 200D · 300D · 1Y · 2Y · 3Y** |
| Main driver | Momentum, volume, news, sentiment | Rule-based quality/valuation score **+** ML return forecast |
| Data frequency | End-of-day + hourly snapshots | End-of-day prices, quarterly / yearly financials |
| Output % | Expected % move + probability up + entry/exit | Target % for a holding period + fair-value upside % + entry/exit |
| Refresh | Daily | Predictions nightly; fundamentals after results |
| Risk focus | Volatility, stop-loss | Debt, stability, drawdowns |

## Entry & exit
Every recommendation comes with **when to enter, how long to hold and when to exit**. See [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md).

## Combined view (later, once short-term exists)
Merges both engines into one summary card and highlights where they disagree
(e.g., "short-term weak, long-term strong" → possible buying opportunity).

## Percentage outputs: where each is shown
✅ Decision (Q4). Example: RELIANCE at ₹1,000, 50-day category.

| Output | Meaning | Example | Shown in |
|---|---|---|---|
| **Expected return % + range** (headline) | Median predicted return and the p10–p90 range | **+9%** (−6% … +24%) | Stock view, screener |
| **Probability of hitting the target** (headline) | Chance of reaching the target % before the stop-loss | **41%** chance of +20% | Stock view, screener, journal (locked at start) |
| Probability up | Chance of any gain at the end of the period | 64% | Stock view (secondary) |
| **CAGR** | Return per year, to compare long holds fairly | 3Y +44% ≈ **13%/yr** vs 1Y 15%/yr | Holding-period comparison, **1Y and longer only** (misleading for short holds) |
| **P/L %** | Real gain/loss of your plans, vs NIFTY 50 | +5.0% (day 12/50); all plans +3.2% vs NIFTY +1.8% | Trade journal, daily report |

Headline format everywhere: *"+9% (−6…+24%) · 41% chance of +20%"*.

## Current focus
1. **Long-term first** (50 days – multi-year); short-term later
2. **First capability:** the manual [15 – Trade Journal (Manual Tracking) 📒](15-trade-journal.md): select stock → start date → holding days → predicted % → mark outcome & exit
3. Then the [16 – Holding-Period Screener 🔎](16-holding-period-screener.md): "50 days, 20% → which stocks?"

## Operating model
- **Pure mathematical prediction:** statistical/ML models on numeric data only; OpenAI only if required, never for numbers
- **Runs 24/7** as a self-hosted Docker stack, see [14 – Docker Deployment & 24/7 Operation 🐳](14-docker-deployment.md)
- **Data:** direct-connect APIs configured in the admin UI; hourly snapshots + end-of-day ([04](04-data-sources.md), [22](22-provider-configuration-ui.md))
- **Environments:** dev/test locally in Docker; prod on a Linux server later ([20](20-environments-dev-test-prod.md))
- **End-of-day returns report** every trading day, see [13 – End-of-Day Returns Report 📊](13-daily-returns-report.md)

## Guiding principles
- Always show **ranges and confidence**, never a single certain number.
- Every model must beat a simple baseline.
- Predictions are analysis, **not financial advice**.

## Related
- [02 – Short-Term Analyzer 🟢](02-short-term-analyzer.md)
- [03 – Long-Term Analyzer 🔵](03-long-term-analyzer.md)
- [09 – Roadmap](09-roadmap.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](00-how-to-plan.md) · [🏠 Index](README.md) · [Next →](02-short-term-analyzer.md)
