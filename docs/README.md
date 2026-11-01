# Stock Analyzer – Planning Docs

Planning documents for a stock analysis and prediction application: **Python (FastAPI) backend + React frontend**, running in Docker.

**Status:** ✅ Planning complete → **Phase 1 – Foundation as a POC on synthetic data** ([27 – Phase 1 POC Plan](27-phase1-poc-plan.md))

## Key decisions at a glance
| Area | Decision |
|---|---|
| Market | 🇮🇳 India (NSE; BSE optional) now, world markets later · NIFTY 50 first, then all NSE stocks |
| Focus | 🔵 **Long-term first** (50D · 100D · 200D · 300D · 1Y · 2Y · 3Y); 🟢 short-term (1 day – 2 weeks) later |
| First capability | 📒 Manual trade journal, then the 🔎 holding-period screener |
| Predictions | Pure statistics / ML (LightGBM per holding category, calibrated ranges), retrained weekly; OpenAI only if required (never for numbers) |
| Data | **No broker, no orders.** Journal values entered manually; prices + fundamentals from data-only APIs configured in the **admin UI**; hourly snapshots + end-of-day |
| Stack | FastAPI · PostgreSQL + TimescaleDB + pgvector · React + TypeScript (Vite) |
| Code | Clean Architecture, OOP, strict naming and quality rules ([24](24-coding-standards.md)) |
| Runs on | Docker on Linux, macOS or Windows + WSL2; dev/test local, prod on Linux later |
| Users | Personal + other users: **OAuth sign-in (Google / Microsoft) + invite code** to sign up |
| Later phases | WhatsApp notifications, remote access via hosted deployment |

Full decision log: [Open Questions & Decision Log 🗳️](decisions/open-questions.md) · Everything to set up: [25 – Infrastructure, Services & Requirements Inventory 🧰](25-infrastructure-services-inventory.md).

| # | Document | What it covers |
|---|----------|----------------|
| 00 | [How to Plan](00-how-to-plan.md) | Planning steps, checklist, doc template, linking rules |
| 01 | [Overview & Goals](01-overview.md) | Vision, scope, the two analysis modes, current focus |
| 02 | [Short-Term Analyzer](02-short-term-analyzer.md) | ⏭️ Later phase · 1 day – 2 weeks: technicals, ML models, signals |
| 03 | [Long-Term Analyzer](03-long-term-analyzer.md) | 50 days – multi-year: rule-based score + ML forecast per holding category |
| 04 | [Data Sources](04-data-sources.md) | Data-only APIs (prices + fundamentals), no broker; nothing self-maintained |
| 05 | [Models & Evaluation](05-models-and-evaluation.md) | Prediction approaches, metrics, backtesting |
| 06 | [App Features & UI](06-app-features.md) | Features by phase: stock view, journal, screener, reports, admin |
| 07 | [Architecture & Tech Stack](07-architecture.md) | System diagram, daily data flow, tech stack |
| 08 | [Non-Functional Requirements](08-non-functional.md) | Reliability, security, retraining, disclaimers |
| 09 | [Roadmap](09-roadmap.md) | Phased build plan |
| 10 | [AI / LLM Integration](10-ai-llm-integration.md) | Optional: OpenAI if required, local on Apple Silicon / NVIDIA; never for numbers |
| 11 | [Live Cloud Data](11-live-cloud-data.md) | Hourly + end-of-day data, schedule, (optional) broker comparison |
| 12 | [Entry & Exit Strategy](12-entry-exit-strategy.md) | When to enter, holding period, target %, stop-loss, exit rules |
| 13 | [End-of-Day Returns Report](13-daily-returns-report.md) | Daily actual vs predicted returns for journal plans, accuracy, WhatsApp later |
| 14 | [Docker Deployment & 24/7](14-docker-deployment.md) | Containers, 24/7 IST schedule, reliability, host setup |
| 15 | [Trade Journal](15-trade-journal.md) | Manual tracking: stock, start, holding days, predicted %, outcome, exit |
| 16 | [Holding-Period Screener](16-holding-period-screener.md) | 50D … 3Y categories; filter by target %; best horizon per stock |
| 17 | [Database & Backend](17-database-backend.md) | PostgreSQL + TimescaleDB + pgvector, FastAPI, tables, logging |
| 18 | [Methods, Accuracy & References](18-methods-accuracy-references.md) | Industry-standard logic, realistic accuracy, GitHub projects |
| 19 | [Authentication & Multi-User](19-auth-multi-user.md) | OAuth/OIDC sign-in, roles, data licence, SEBI, privacy |
| 20 | [Environments: Dev, Test & Prod](20-environments-dev-test-prod.md) | Local Docker dev/test, Linux prod, compose overrides, testing, deploys |
| 21 | [Stock Analysis Data Points](21-stock-analysis-datapoints.md) | 🔬 Draft under research: every data point, formula, thresholds, red flags, weights + research tracker |
| 22 | [Data Provider Configuration UI](22-provider-configuration-ui.md) | Admin screen to add, test, prioritise and switch providers; plugins, failover, encrypted keys |
| 23 | [Frontend (React) & Backend](23-frontend-react.md) | React + TypeScript (Vite) stack, pages, API endpoints, Docker, repo layout |
| 24 | [Coding Standards & Clean Architecture](24-coding-standards.md) | Layers, OOP patterns, naming conventions, folder structure, quality rules, Definition of Done |
| 25 | [Infrastructure, Services & Requirements](25-infrastructure-services-inventory.md) | Everything needed: infra, Docker services, accounts, tools, ports, config, costs, setup checklist |
| 26 | [ML Pipeline & Model Operations](26-ml-pipeline.md) | Features, labels, training, quality gates, registry, nightly predictions, monitoring |
| 27 | [Phase 1 POC Plan](27-phase1-poc-plan.md) | Synthetic-data POC: scope, data generator, baseline predictions, milestones M0–M7 |
| 28 | [UI/UX Redesign Plan](28-ui-ux-redesign-plan.md) | End-to-end redesign: diagnosis, journeys, screens, design system, mockups-first process, milestones UI-0–UI-6 |

## Decision log
Every question and decision: [🗳️ decisions/open-questions.md](decisions/open-questions.md) (stable path, not numbered).

## Deliverables & outcomes
What "done" means for every phase, with acceptance criteria and evidence: [🎯 deliverables/](deliverables/README.md).

## Start here
New to these docs? Read [00 – How to Plan This Project](00-how-to-plan.md) first, then follow the **Next →** links.
