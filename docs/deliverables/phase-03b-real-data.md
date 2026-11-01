[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-03-long-term-engine.md) · [Next phase →](phase-04-screener.md)

# Phase 3b – Real Market Data (EODHD)

**Phase outcome:** With an API key entered in the admin UI, real NSE prices and fundamentals replace the synthetic data, so the ML engine (Phase 3) can be judged on real data.
**Status:** 🟡 Built and verified with fixtures; waiting for your EODHD key (live check + `make real-data`) · **Branch:** `feature/real-data-eodhd` · **Plan:** [22 – Provider Configuration UI](../22-provider-configuration-ui.md), [04 – Data Sources](../04-data-sources.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D3b.1 | Encrypted credentials | API keys are entered in the admin UI, stored encrypted and never shown or logged in full | ✅ |
| D3b.2 | EODHD plugin | Daily prices and quarterly fundamentals for NSE stocks come from EODHD through the existing provider ports | 🟡 Built; live check needs your key |
| D3b.3 | Provider selection & switch | The admin chooses the primary provider; one command replaces synthetic data with real data | ✅ |
| D3b.4 | Admin UI | Providers page: enter/replace/remove the key, test the connection (with quota), set primary | ✅ |

---

### D3b.1 – Encrypted credentials
**Outcome:** API keys are entered in the admin UI, stored encrypted and never shown or logged in full.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Fernet encryption with `SA_MASTER_KEY` behind a `SecretCipher` port; a missing key refuses to store secrets | Unit tests (round trip, wrong key fails) | ✅ 2026-11-01: `FernetCipher`; `test_fernet_round_trip_and_wrong_key` |
| 2 | `PUT`/`DELETE /api/admin/providers/{plugin}/credentials`; responses and listings show only the last 4 characters | e2e tests | ✅ 2026-11-01: `test_admin_providers_api.py` (write-only, hints, validation, 404) |
| 3 | No secret in logs or errors: HTTP client logging is silenced and error messages mask the token | Unit test with a captured log | ✅ 2026-11-01: httpx/httpcore logging at WARNING; `test_bad_key_gives_a_clear_error_without_the_token` |

---

### D3b.2 – EODHD plugin
**Outcome:** Daily prices and quarterly fundamentals for NSE stocks come from EODHD through the existing provider ports.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | `EodhdProvider` implements `MarketDataProvider` and `FundamentalsProvider` (`{SYMBOL}.NSE`, `/api/eod`, `/api/v1.1/fundamentals` with `filter`) | Integration tests against recorded HTTP fixtures (no network) | ✅ 2026-11-01: `test_eodhd_provider.py` against fixture responses via `httpx.MockTransport` |
| 2 | Retries with back-off on 429 / 5xx; a 401/403 gives a clear "check the API key" error | Unit tests with a fake transport | ✅ 2026-11-01: `test_retries_on_rate_limit_then_succeeds`; 401 → 'check it in Admin' |
| 3 | Fundamentals are point-in-time: the announcement date comes from the earnings report date (fallback: quarter end + 45 days) | Unit test | ✅ 2026-11-01: `test_fundamentals_map_to_crore_and_point_in_time`, `test_fundamentals_respect_the_as_of_date` |
| 4 | Test connection calls `/api/user` and reports the daily quota used | Unit test | ✅ 2026-11-01: `test_connection_reports_the_quota` |
| 5 | Field mapping checked against one **live** response once a key is available | Recorded fixture from the live API | ⬜ Needs your EODHD key: save it, run Test connection, then replace `tests/fixtures/eodhd/*` with a live response |

---

### D3b.3 – Provider selection & switch
**Outcome:** The admin chooses the primary provider; one command replaces synthetic data with real data.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Primary market-data/fundamentals provider per market stored in `provider_assignments` (default: mock) | e2e test | ✅ 2026-11-01: `test_primary_needs_credentials_and_blocks_removal`; DB test |
| 2 | `make real-data` (asks for confirmation): deletes synthetic prices, fundamentals, features and labels, backfills from the primary provider, then runs features → train → predict | Integration test with a fake provider; dry run on dev | ✅ 2026-11-01: `test_replaces_synthetic_data_and_keeps_the_journal`, `test_refuses_while_mock_is_primary`; not run on dev (needs a key) |
| 3 | Stocks loaded from a real provider lose the SYNTHETIC badge (`source_provider`) | e2e test | ✅ 2026-11-01: `source_provider == "eodhd"` after the switch (same test) |
| 4 | Journal plans and their locked predictions are kept | Integration test | ✅ 2026-11-01: plans unchanged after the switch (same test) |

---

### D3b.4 – Admin UI
**Outcome:** Providers page: enter/replace/remove the key, test the connection (with quota), set primary.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Password field, masked hint (•••• 1a2b), save / remove; the key is never sent back to the browser | Playwright | ✅ 2026-11-01: `providers.e2e.mjs` (key never in the page after saving) |
| 2 | Test button shows the result and the quota message; "Use as primary" switch | Playwright + visual baseline | ✅ 2026-11-01: `providers.e2e.mjs`; `providers-*.png` baselines |

---

## Phase exit criteria
- [ ] All deliverables ✅ (D3b.2 #5 needs your API key)
- [x] `make lint`, `make test`, `make e2e` pass in containers (2026-11-01: 145 backend + 76 frontend)
- [x] Docs and Open Questions updated (Q65; doc 22)
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Built: credentials, EODHD plugin, primary, `make real-data`, Providers UI | Waiting for an API key for the live check |
| 2026-11-01 | Phase defined | Phase 3's outcome needs real data |

## Related
- [Phase 3 – Long-Term Engine](phase-03-long-term-engine.md)
- [22 – Provider Configuration UI](../22-provider-configuration-ui.md)
- [04 – Data Sources](../04-data-sources.md) (EODHD India coverage, plans and API calls per day)

---
[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-03-long-term-engine.md) · [Next phase →](phase-04-screener.md)
