<!-- nav -->[← Previous](07-architecture.md) · [🏠 Index](README.md) · [Next →](09-roadmap.md)

# 08 – Non-Functional Requirements

**Purpose:** reliability, security, maintenance, quality and compliance requirements across the whole system.

## Reliability & data quality
- Handle API rate limits with caching and retries
- Handle missing data, splits, dividends and holidays
- Validate data before it reaches the models
- Automatic provider failover (primary → fallback) and a `source_provider` on every record ([22](22-provider-configuration-ui.md))
- Jobs are idempotent and catch up after downtime ([14](14-docker-deployment.md))

## Model maintenance
- Retrain the long-term models weekly (weekends), because accuracy degrades as markets change
- Recompute scores after each results announcement; predictions run nightly
- Short-term models (later) retrain weekly or monthly
- Version models and log their performance over time

## Security
- Provider credentials are entered in the **admin UI** and **encrypted in the database**; shown masked, never logged ([22](22-provider-configuration-ui.md))
- `.env` holds only bootstrap values (database URL, master encryption key) and is never committed to git
- Separate secrets per environment (dev / test / prod) ([20](20-environments-dev-test-prod.md))

## Authentication
- OAuth 2.0 / OIDC sign-in, roles and per-user data. See [19 – Authentication (OAuth) & Multi-User 🔐](19-auth-multi-user.md)

## Quality
- Coding standards, layers and Definition of Done in [24 – Coding Standards & Clean Architecture 📏](24-coding-standards.md)
- Structured JSON logging and a `job_runs` table ([17](17-database-backend.md#logging))
- Unit tests for data points and valuation formulas; tests that check for data leakage (no future data in training)

## Portability
- Runs in Docker on Linux, macOS and Windows + WSL2 ([20](20-environments-dev-test-prod.md#supported-host-platforms))
- Market-agnostic design: India first, world markets later ([01](01-overview.md))

## Compliance & transparency
- Clear disclaimer: analysis only, not financial advice
- 🇮🇳 **SEBI:** giving buy/sell recommendations to *other people* (especially for a fee) can require SEBI Research Analyst registration. Personal use is fine; get advice before offering it publicly.
- Show confidence and the reasons behind each signal
- 🇮🇳 **DPDP Act 2023:** with other users, keep only the necessary personal data and allow deletion ([19](19-auth-multi-user.md))
- Market data licence: personal-use API data must not be redistributed to other users ([19](19-auth-multi-user.md))

## Related
- [05 – Models & Evaluation](05-models-and-evaluation.md)
- [11 – Live Cloud Data (Actual Values)](11-live-cloud-data.md)
- [🏠 Index](README.md)

---
<!-- nav -->[← Previous](07-architecture.md) · [🏠 Index](README.md) · [Next →](09-roadmap.md)
