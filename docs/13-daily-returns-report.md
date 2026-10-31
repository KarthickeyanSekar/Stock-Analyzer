<!-- nav -->[← Previous](12-entry-exit-strategy.md) · [🏠 Index](README.md) · [Next →](14-docker-deployment.md)

# 13 – End-of-Day Returns Report 📊

**Purpose:** every trading day after market close, report the **actual returns** of all active predictions and trade plans,
and compare them with what was predicted. This is how the system proves whether it works.

> No model can guarantee a return. This report shows the **real, measured** results, profit or loss, every day.

## When it runs
| Time (IST) | Job |
|---|---|
| 15:30 | Market closes |
| 15:45 – 17:00 | Fetch closing prices from the market data API (NSE, BSE optional) |
| 16:00 | Update every open position and closed trade; compute returns |
| 16:15 | Generate the report and send notifications |
| 18:00 | Re-fetch the final EOD candles from the market data API; correct any differences |

Skip on NSE holidays (use the NSE holiday calendar).

## Pure mathematical approach
Predictions come only from **mathematical / statistical / ML models** on numeric data
(prices, volume, indicators, fundamentals). LLMs are **off by default**
([10 – AI / LLM Integration (OpenAI or Local Models)](10-ai-llm-integration.md) is an optional add-on).
Every number in the report is calculated, never generated.

## What is tracked
1. **First: trade journal plans** ([15](15-trade-journal.md)), the plans you start and close yourself
2. **Later (optional): automated paper trading**, where each signal opens a virtual position automatically

### Automated paper trading (later)
- **Starting capital is custom:** each user sets it in Settings › Paper trading (stored in `user_settings`); it can be reset, which starts a new tracking period
- Each signal opens a **virtual position** at the next day's open price (no look-ahead)
- Exits follow the rules in [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md)
- Costs (brokerage, STT, charges) are deducted so returns are **net**
- Real-money orders only later, and only if you choose them (see [Open Questions](28-open-questions.md))

## Report contents
```
📊 Daily Returns – 2026-10-27 (Tue)

TODAY
  Portfolio (paper):   ₹10,24,350   Day P/L: +₹6,120 (+0.60%)   NIFTY 50: +0.35%
  Open positions: 8    New entries: 2    Exits: 1

CLOSED TODAY
  INFY   🔵 50D  held 48 days   +11.0% net  🟡 PARTIAL (predicted +10%, tuning required)

OPEN POSITIONS
  Stock     Engine  Day  Entry    Now      Return   Target  Stop   Predicted
  RELIANCE  🔵 LT   12/50 ₹2,900  ₹3,045   +5.0%    +20%    −7%    +9% median
  TCS       🟢 ST   3/10  ₹4,120  ₹4,080   −1.0%    +4%     −2.5%  +2.1%

MODEL ACCURACY (rolling 30 days)
  Short-term direction accuracy: 56%    Calibration error: 4%
  Win rate: 58%   Avg win: +3.9%   Avg loss: −2.1%   Expectancy: +1.4%/trade

CUMULATIVE
  Since start: +7.8%   vs NIFTY 50: +4.1%   Max drawdown: −3.6%
```

## Metrics tracked
| Metric | Meaning |
|---|---|
| Day P/L (₹ and %) | Today's change across all positions |
| Net return per trade | After costs and charges |
| Predicted vs actual | Error of each prediction |
| Directional accuracy | % of correct up/down calls |
| Calibration | Do "60% probability" calls succeed about 60% of the time? |
| Win rate, expectancy | Quality of the trade plans |
| Cumulative return vs NIFTY 50 | Is it beating the index? |
| Max drawdown | Worst fall from a peak |

## Delivery
- Reports page in the React app (`/reports`) with history charts
- **In-app notification** in the dashboard every evening (no external channel for now)
- CSV / PDF archive for each day
- Stored in the database (`daily_returns`, `positions`, `predictions` tables)

## Notification channels (later)
✅ **Next phase: WhatsApp** via the official WhatsApp Business Platform (Cloud API). In-app notifications until then.

| Option | How | Notes |
|---|---|---|
| **WhatsApp Business Platform (Cloud API, by Meta)** | Official API; a business number + Meta Business verification | ✅ Official. Messages the app starts (like the daily report) must use **pre-approved message templates**, and Meta charges per message (check current pricing) |
| WhatsApp via Twilio / other BSPs | Same official API through a provider | Easier setup, provider fee on top |
| ❌ Unofficial libraries (WhatsApp Web automation) | Scripts a personal WhatsApp account | Breaks WhatsApp's terms; the number can be **banned**. Not used |
| Telegram bot / email | Free and simple | Fallback options if WhatsApp's cost or approval becomes a problem |

Design now so it's easy to add later: a `Notifier` interface (`send_report()`, `send_alert()`) with an in-app implementation first;
WhatsApp becomes another implementation chosen by config. With other users, each user opts in to WhatsApp messages (required by WhatsApp's policy).

## Related
- [12 – Entry & Exit Strategy ⏱️](12-entry-exit-strategy.md)
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [14 – Docker Deployment & 24/7 Operation 🐳](14-docker-deployment.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](12-entry-exit-strategy.md) · [🏠 Index](README.md) · [Next →](14-docker-deployment.md)
