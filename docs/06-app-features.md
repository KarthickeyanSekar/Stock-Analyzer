<!-- nav -->[← Previous](05-models-and-evaluation.md) · [🏠 Index](README.md) · [Next →](07-architecture.md)

# 06 – App Features & UI

**Purpose:** what users can do in the React app, by phase. Pages and routes are in [23 – Frontend (React) & Backend Split 🖥️](23-frontend-react.md#pages).

## Features by phase
| Feature | What it does | Phase |
|---|---|---|
| ⚙️ **Data providers (admin)** | Add, test, prioritise and switch providers ([22](22-provider-configuration-ui.md)) | 1 |
| 📈 **Stock view** | Search a stock; candlestick chart with moving averages; analysis card with data point scores ([21](21-stock-analysis-datapoints.md)) | 1–3 |
| 📒 **Trade journal** | Start a plan (stock, start date, holding category, locked prediction), daily tracking, mark outcome and exit ([15](15-trade-journal.md)) | 2 |
| ⚙️ **Settings** | Paper capital (custom), risk per trade (custom, default 1%), success tolerance (default ±0.5 pp), preferences | 2 |
| 🔵 **Long-term predictions** | Median %, range and probability for each holding category (50D … 3Y) | 3 |
| 🔎 **Holding-period screener** | "50 days, 15–25% → which stocks?"; best holding period per stock ([16](16-holding-period-screener.md)) | 4 |
| 🔐 **Sign-in & users** | OAuth (Google / Microsoft), sign-up with a shared **invite code**, roles, admin can create/revoke codes and disable accounts ([19](19-auth-multi-user.md)) | 5b |
| 📊 **Daily returns report** | Actual vs predicted for every active plan; accuracy and calibration ([13](13-daily-returns-report.md)) | 6 |
| 🔔 **Alerts** | Target reached, stop-loss crossed, plan end date, data/job failures (in-app) | 6 |
| 📱 **WhatsApp notifications** | Daily report + alerts ([13](13-daily-returns-report.md#notification-channels-later)) | 5c / later |
| 🟢 **Short-term tab** | 1 day – 2 weeks signals ([02](02-short-term-analyzer.md)) | 7 / later |
| 🔀 **Combined card** | Short-term + long-term together | Later |
| ⭐ Watchlist, compare stocks, CSV / PDF export | Convenience features | Later |

## Example: combined card (later)
```
HDFC Bank
Short-term:  📈 64% chance up, +2% in 5 days
Long-term:   💎 Undervalued, 18% upside, quality 9/10
Combined:    Strong – good for both trading and holding
```

## Related
- [01 – Overview & Goals](01-overview.md)
- [23 – Frontend (React) & Backend Split 🖥️](23-frontend-react.md)
- [07 – Architecture & Tech Stack](07-architecture.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](05-models-and-evaluation.md) · [🏠 Index](README.md) · [Next →](07-architecture.md)
