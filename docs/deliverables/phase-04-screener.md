[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-03-long-term-engine.md) · [Next phase →](phase-05-validation.md)

# Phase 4 – Holding-Period Screener

**Phase outcome:** A user can ask 'N days, X% → which stocks?' and get ranked results with ranges and probabilities in seconds.
**Status:** ⚪ Not started · **Branch:** _when started_ · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D4.1 | Screener query | Filter by category, target % (range), min probability, max stop, quality, sector | ⚪ |
| D4.2 | Stock horizon view | For one stock, all categories side by side with the best risk-adjusted one marked | ⚪ |
| D4.3 | Historical analogs | Similar past setups found via pgvector with their outcomes | ⚪ |
| D4.4 | Performance | Screener responds in < 2 s for all NSE stocks | ⚪ |

---

### D4.1 – Screener query
**Outcome:** Filter by category, target % (range), min probability, max stop, quality, sector.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Filter by category, target % (range), min probability, max stop, quality, sector | e2e tests | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D4.2 – Stock horizon view
**Outcome:** For one stock, all categories side by side with the best risk-adjusted one marked.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | For one stock, all categories side by side with the best risk-adjusted one marked | Screenshot | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D4.3 – Historical analogs
**Outcome:** Similar past setups found via pgvector with their outcomes.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Similar past setups found via pgvector with their outcomes | Integration test | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D4.4 – Performance
**Outcome:** Screener responds in < 2 s for all NSE stocks.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Screener responds in < 2 s for all NSE stocks | Load test | ⬜ |

_Detailed criteria are added when the phase is planned._

---

## Phase exit criteria
- [ ] All deliverables ✅
- [ ] `make lint` and `make test` pass in containers
- [ ] Docs and Open Questions updated
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
