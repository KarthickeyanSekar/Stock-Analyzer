[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-01-foundation-poc.md) · [Next phase →](phase-03-long-term-engine.md)

# Phase 2 – Trade Journal

**Phase outcome:** Users can track holding plans manually, end to end, with honest calculated outcomes on real or synthetic prices.
**Status:** ⚪ Not started · **Branch:** _when started_ · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D2.1 | Journal decisions | Q28 (calendar vs trading days), Q29 (entry price) and Q31 (own target %) are decided and implemented | ⚪ |
| D2.2 | Daily plan tracking | Active plans show day N of M, current return and progress to target, updated from hourly/EOD prices | ⚪ |
| D2.3 | Stop-loss & time stop | Plans flag target reached, stop-loss crossed and end date reached automatically | ⚪ |
| D2.4 | Settings | Paper capital, risk % (default 1%) and tolerance (default ±0.5 pp) are configurable; suggested amount shown | ⚪ |
| D2.5 | Track record | Success / partial / failure rates per category and actual vs predicted are shown | ⚪ |

---

### D2.1 – Journal decisions
**Outcome:** Q28 (calendar vs trading days), Q29 (entry price) and Q31 (own target %) are decided and implemented.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Q28 (calendar vs trading days), Q29 (entry price) and Q31 (own target %) are decided and implemented | Q28/Q29/Q31 ✅; behaviour covered by tests | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D2.2 – Daily plan tracking
**Outcome:** Active plans show day N of M, current return and progress to target, updated from hourly/EOD prices.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Active plans show day N of M, current return and progress to target, updated from hourly/EOD prices | Integration test with price fixtures; screenshot | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D2.3 – Stop-loss & time stop
**Outcome:** Plans flag target reached, stop-loss crossed and end date reached automatically.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Plans flag target reached, stop-loss crossed and end date reached automatically | Unit + integration tests | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D2.4 – Settings
**Outcome:** Paper capital, risk % (default 1%) and tolerance (default ±0.5 pp) are configurable; suggested amount shown.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Paper capital, risk % (default 1%) and tolerance (default ±0.5 pp) are configurable; suggested amount shown | e2e test | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D2.5 – Track record
**Outcome:** Success / partial / failure rates per category and actual vs predicted are shown.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Success / partial / failure rates per category and actual vs predicted are shown | Screenshot; SQL check | ⬜ |

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
