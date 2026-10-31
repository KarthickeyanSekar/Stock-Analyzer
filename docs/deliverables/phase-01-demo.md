[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [Phase 1](phase-01-foundation-poc.md)

# Phase 1 POC – Demo Script 🎬

**Goal:** from a fresh clone to a closed journal plan with a calculated outcome, on **synthetic data**.
Everything you see is labelled **SYNTHETIC DATA**: these are generated prices, not real market data.

## Setup (once)
| # | Step | Command | Expected |
|---|---|---|---|
| 1 | Clone | `git clone https://github.com/KarthickeyanSekar/Stock-Analyzer.git && cd Stock-Analyzer` | Repo on disk |
| 2 | Bootstrap | `make bootstrap` | `.env` with generated secrets; db + Redis running; migrations `0003 (head)`; 50 stocks, 64,300 candles, 350 predictions |
| 3 | Start the app | `make dev` | Web on http://localhost:5173, API docs on http://localhost:8000/docs, Grafana on http://localhost:3000 |

Already set up? `make poc-data` reloads the synthetic data and predictions (safe to re-run).

## Walkthrough
| # | Step | Where | What to check |
|---|---|---|---|
| 4 | Open **Stocks** | http://localhost:5173/stocks | 50 NIFTY 50 stocks; red **SYNTHETIC DATA** badge in the top bar |
| 5 | Search `bank`, open **HDFCBANK** | Stock page | Candlestick chart; last close in ₹; predictions table for 50D … 3Y |
| 6 | Read a prediction row | Predictions card | Headline like `+9% (−6%…+24%) · 41% chance of +20%`; CAGR shown only for 1Y, 2Y, 3Y; change the **Target** selector to see other targets |
| 7 | Start a plan | **Start a plan** card | Choose `1Y`, leave entry price and target empty → "Plan #N started: target …%, ends …. Prediction locked." (If the predicted median is not positive, the app asks you to enter a target) |
| 8 | See the plan on the chart | Price card | Entry, target and stop lines drawn on the chart |
| 9 | Close the plan | **Journal** page | Enter an exit price ≈ the target price → **✅ Success**; above → **🟡 Partial · tuning required**; below → **❌ Failure** (tolerance ±0.5 pp) |
| 10 | Check providers | **Providers** page | `Mock (synthetic data)` listed; **Test connection** → 🟢 OK |

## Verify from the command line (optional)
```bash
curl -s localhost:8000/api/stocks/RELIANCE/predictions | python3 -m json.tool | head -30
curl -s localhost:8000/api/trade-plans | python3 -m json.tool
make db-shell     # then: select category, count(*) from predictions group by category;
```

## Known POC limits
- Data is synthetic (mock provider). Real data needs a provider plugin (e.g., EODHD) configured in Admin › Providers.
- Predictions are the **empirical baseline** (past forward returns), not ML models yet (Phase 3).
- No sign-in yet (Phase 5b); everyone sees the same journal.
- Fundamentals are not generated yet, so the analysis card from doc 21 isn't shown.

## Related
- [Phase 1 deliverables](phase-01-foundation-poc.md)
- [27 – Phase 1 POC Plan (Synthetic Data) 🧪](../27-phase1-poc-plan.md)
