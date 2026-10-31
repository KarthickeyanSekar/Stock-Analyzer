[🏠 Docs index](../README.md) · [🎯 Deliverables](../deliverables/README.md) · [🗺️ Roadmap](../09-roadmap.md)

# Open Questions & Decision Log 🗳️

**Purpose:** the single log of every project decision: what was asked, the options, and what was decided.
This file lives **outside the numbered docs** so adding a new doc never renames it (stable path, clean git history).

**Status markers:** ✅ decided · _TBD_ open · ⏭️ deferred to a later phase · Proposed = recommendation awaiting confirmation.
**Rules:** new questions are **appended** with the next number; numbers are never reused or reordered; when a question is decided,
update its row **and** every doc it affects.


| # | Question | Options | Decision |
|---|---|---|---|
| 1 | Which market? | India (NSE/BSE), US, both, crypto | ✅ **India (NSE/BSE) now**; **world markets later** (design stays market-agnostic) |
| 2 | Short-term horizon? | 1 day, 5 days, 2 weeks | ✅ **1 day – 2 weeks** |
| 3 | Long-term method? | Rule-based scoring, ML forecast, both | ✅ **Both** (score + ML return forecast, e.g., "hold 50 days → +20%") |
| 4 | Main "percentage" output? | % change, probability up, CAGR, portfolio P/L | ✅ **Headline: expected return % with range (p10–p90) + probability of hitting the target**; CAGR only for 1Y+ to compare holding periods; P/L % in the journal and reports ([01](../01-overview.md#percentage-outputs-where-each-is-shown)) |
| 5 | Who uses it? | Personal / learning, or other users | ✅ **Pet project: personal + other users**, with OAuth sign-in ([19](../19-auth-multi-user.md)) |
| 6 | Interface? | Streamlit, React, CLI | ✅ **React + TypeScript (Vite) frontend + FastAPI backend** ([23](../23-frontend-react.md)) |
| 7 | Data budget? | Free only, or paid APIs | _TBD_ |
| 8 | Which stocks to start with? | Watchlist of 10–20, an index (NIFTY 50) | ✅ **NIFTY 50 first**, then expand to **all NSE-listed stocks** (~2,000+) |
| 9 | LLM provider? | OpenAI, local (Ollama/LM Studio), both via config | ✅ **OpenAI, only if required.** All predictions use **pure statistics/ML**; the LLM never produces numbers |
| 10 | Local hardware for LLMs? | Apple Silicon, NVIDIA GPU | ✅ **Both**: Apple Silicon for local dev, NVIDIA GPU for the Linux prod server ([10](../10-ai-llm-integration.md#local-llm-hardware-apple-silicon--nvidia)) |
| 11 | Data freshness needed? | Real-time streaming, 15-min delayed, hourly, end-of-day | ✅ **Hourly snapshots + end-of-day** (no intraday trading) |
| 12 | Paid data API budget? | Free only, paid | ✅ **Paid managed APIs accepted** (direct connect, no self-maintained pipelines) |
| 13 | Entry/exit style? | Fixed target + stop, trailing stop, time stop, combination | ✅ **Combination**: fixed target + fixed stop-loss + time stop (planned end date); trailing stop optional per plan, off by default. Whichever happens first ends the plan ([12](../12-entry-exit-strategy.md#-decision-exit-style--combination)) |
| 14 | Default risk per trade? | 1%, 2%, custom | ✅ **Custom per user, default 1%** (changeable in Settings); the app suggests the position size ([12](../12-entry-exit-strategy.md#4-position-sizing--risk)) |
| 15 | Which broker account (for live data, later for orders)? | Upstox (free), Angel One (free, TOTP), Dhan (₹499/mo, no daily login), Zerodha (₹500/mo) | ✅ **None for now.** No broker account is connected; values are entered **manually** in the app. A broker can be added later in the admin UI ([22](../22-provider-configuration-ui.md)) |
| 16 | Automated order placement? | No (signals only), later via broker API | ✅ **No.** The app never places orders; signals and tracking only. Order placement is a possible future feature |
| 17 | Deployment? | Cloud VM, self-hosted Docker | ✅ **Self-hosted Docker Compose, 24/7** |
| 18 | Host machine OS & specs? | Linux server, Mac, Windows + WSL | ✅ **All three supported as hosts** (Linux, macOS, Windows + WSL2). Prod recommended on a Linux server. See [20](../20-environments-dev-test-prod.md#supported-host-platforms) |
| 19 | Starting paper capital? | ₹1 lakh, ₹10 lakh, custom | ✅ **Custom**: each user sets their own starting capital in the app (Settings › Paper trading) |
| 20 | Report channel? | Telegram, email, WhatsApp | ✅ **Next phase: WhatsApp** (official WhatsApp Business Cloud API). Until then, reports and alerts are shown in the dashboard ([13](../13-daily-returns-report.md#notification-channels-later)) |
| 21 | Remote access to the dashboard? | Local network only, Tailscale VPN, Cloudflare Tunnel, reverse proxy, hosted deployment | ✅ **Not required.** Local access only. If remote access is ever needed, the solution will be **deployed to a hosted server** (e.g., a cloud Linux VM) instead of exposing the home machine |
| 22 | Data integration approach? | Self-built (scrapers, bhavcopy, XBRL), direct-connect managed APIs | ✅ **Direct connect only** |
| 23 | Which fundamentals API? | EODHD, Financial Modeling Prep, Trendlyne, Tijori | _TBD_ (check NSE small-cap coverage) |
| 24 | Build order? | Short-term first, long-term first, both | ✅ **Long-term first** (50 days – multi-year); short-term later |
| 25 | First capability? | Auto paper trading, manual trade journal | ✅ **Manual trade journal** + holding-period screener |
| 26 | Database? | SQLite, PostgreSQL, separate vector DB | ✅ **PostgreSQL + TimescaleDB + pgvector** (no separate vector DB) |
| 27 | Holding categories? | — | ✅ **50D · 100D · 200D · 300D · 1Y · 2Y · 3Y** (5Y optional) |
| 28 | Days entered as calendar or trading days? | Calendar, trading | ⏭️ **Decide in Phase 2** (journal) · Suggested: calendar days in the UI, converted to trading days internally |
| 29 | Entry price for a plan? | Close on the start date (API), my actual buy price | ⏭️ **Decide in Phase 2** (journal) · Suggested: API close by default, editable to the actual buy price |
| 30 | Definition of SUCCESS? | Target reached by end date, any profit at end, beat NIFTY | ✅ **Compared with the predicted %**: equal (within tolerance) = SUCCESS; above = PARTIAL SUCCESS + model tuning required; below = FAILURE ([15](../15-trade-journal.md#-definition-of-success-prediction-accuracy)) |
| 31 | Can I set my own target %, different from the prediction? | Yes, no | ⏭️ **Decide in Phase 2** (journal) · Suggested: yes; the system prediction is stored either way |
| 32 | OAuth approach? | Direct OIDC in FastAPI, managed (Auth0/Clerk/Supabase), self-hosted Keycloak | ✅ **OAuth 2.0 / OIDC** (Google + Microsoft), implemented directly in FastAPI (Authlib) |
| 33 | How will other users get price data legally? | A data plan that allows display to other users, or a redistribution licence from an NSE vendor | _TBD_ |
| 34 | User sign-up? | Invite-only, invite code, open sign-up | ✅ **OAuth + invite code** (default; code shared by an admin, single-use, 7-day expiry, both configurable). Admin can switch to open sign-up. First admin via `SA_ADMIN_EMAILS` ([19](../19-auth-multi-user.md#invite-codes)) |
| 35 | Free or paid for other users? | Free, paid | _TBD_ (paid strengthens the SEBI requirement) |
| 36 | Prod Linux distribution? | Ubuntu 24.04 LTS, Debian 12, other | Proposed: **Ubuntu Server 24.04 LTS** · _TBD_ |
| 37 | Prod server CPU architecture? | x86_64 (amd64), ARM64 | _TBD_ (images are built for both) |
| 38 | Container registry? | GitHub Container Registry, Docker Hub, none (build on server) | Proposed: **GHCR** · _TBD_ |
| 39 | CI for tests? | Local only, GitHub Actions | ✅ **No CI.** All tests run **locally in containers** (`make test`, enforced by pre-commit) |
| 40 | Does the fundamentals API cover promoter pledge, delivery %, ASM/GSM lists and bank NPA/CASA fields? | Check during the API trial | _TBD_ ([21](../21-stock-analysis-datapoints.md)) |
| 41 | Category weights per holding period? | Proposed table in [21](../21-stock-analysis-datapoints.md#weights-by-holding-category), tuned by backtests | 🔬 Under your research · _TBD_ |
| 42 | Exclusion thresholds (liquidity, market cap, pledge)? | Proposed in [21](../21-stock-analysis-datapoints.md#14-exclusion-filters-hard-pass--fail-before-scoring) | 🔬 Under your research · _TBD_ |
| 43 | Deep research of every data point | Tracker in [21](../21-stock-analysis-datapoints.md#research-tracker) | 🔬 In progress (you, separately) |
| 44 | How are data providers configured? | `.env` / code, in-app UI | ✅ **In-app admin UI** with plugins, encrypted credentials and automatic failover ([22](../22-provider-configuration-ui.md)) |
| 45 | Which market data and fundamentals API to start with? | Market data + fundamentals: EODHD, FMP, TrueData, Trendlyne (all in the catalog) | _TBD_ (can be changed later in the UI) |
| 46 | UI component library? | shadcn/ui + Tailwind, MUI, Ant Design, daisyUI | ✅ **shadcn/ui + Tailwind CSS 4** (Radix-based, accessible, code in `shared/ui/`); daisyUI considered but not chosen: CSS-only, so dialogs, comboboxes and menus would need extra code ([23](../23-frontend-react.md#frontend-stack)) |
| 47 | SPA (Vite) or Next.js? | Vite SPA, Next.js | Proposed: **Vite SPA** (backend handles auth and data) · _TBD_ |
| 48 | Coding standards & architecture? | — | ✅ **Clean Architecture + OOP + naming conventions** ([24](../24-coding-standards.md)) |
| 49 | Does the data provider include **delisted stocks** and **historical index membership** (to avoid survivorship bias)? | Check during the API trial | _TBD_ ([26](../26-ml-pipeline.md#1-data-preparation-avoiding-the-classic-traps)) |
| 50 | Experiment tracking / model registry? | MLflow (local container), database only | Proposed: **MLflow** + `model_versions` table · _TBD_ |
| 51 | Model quality gates? | Proposed in [26](../26-ml-pipeline.md#quality-gates-a-new-model-replaces-the-current-one-only-if-all-pass) | Proposed · _TBD_ |

| 52 | Tolerance for "equal to the prediction"? | ±0.5 pp, ±1 pp, ±10% of the predicted value | ✅ **Default ±0.5 percentage points, configurable** (Settings; stored per plan when it starts) |

| 53 | Can regular users create invite codes? | Admins only, users too | Proposed: **admins only** (setting to allow users) · _TBD_ |

| 54 | TimescaleDB on the dev database? (the standalone `-oss` image can't load the default TSL build) | (a) set `timescaledb.license = 'apache'` in the container's server config + restart; (b) switch the container to the full `timescale/timescaledb-ha:pg16` image (as in `compose.yaml`); (c) use compose's own `db` (`make dev-data`) | ✅ **(b) Full image** `timescale/timescaledb-ha:pg16.15-ts2.31.0` (same volume and versions); extensions installed; `compose.yaml` pinned to the same image ([25](../25-infrastructure-services-inventory.md#current-local-dev-setup-verified-2026-10-31)) |
| 55 | Frontend file naming? (code uses kebab-case, doc 24 says PascalCase) | kebab-case files (`trade-plan-table.tsx`, shadcn style), PascalCase files | ✅ **kebab-case file names, PascalCase component names** (matches shadcn/ui and the existing code; doc 24 updated) |
| 56 | Start with a POC on synthetic data? | POC first, real API first | ✅ **POC on synthetic data first** (NIFTY 50 × 5 years, mock provider), then real API integration ([27](../27-phase1-poc-plan.md)) |
| 57 | Where does the decision log live, and how are new docs numbered? | Last numbered doc (renumbered each time), separate folder | ✅ **Separate folder** `docs/decisions/open-questions.md` (stable path); new docs are **appended** with the next number and existing docs are **never renumbered** (keeps links and git history intact) |

## Related
- [00 – How to Plan This Project](../00-how-to-plan.md)
- [09 – Roadmap](../09-roadmap.md)
- [🏠 Index](../README.md)

---
[🏠 Docs index](../README.md) · [🎯 Deliverables](../deliverables/README.md) · [🗺️ Roadmap](../09-roadmap.md)
