[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-05c-whatsapp.md) · [Next phase →](phase-07-short-term.md)

# Phase 6 – Daily Ops

**Phase outcome:** The system runs unattended 24/7 and produces the end-of-day returns report every trading day.
**Status:** ⚪ Not started · **Branch:** _when started_ · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D6.1 | Scheduler | All jobs run on the IST schedule, skip holidays and catch up after downtime | ⚪ |
| D6.2 | EOD report | Daily report with plan P/L, accuracy and calibration | ⚪ |
| D6.3 | Monitoring | Health checks, job failure alerts, provider health, Grafana dashboards | ⚪ |
| D6.4 | Backups | Nightly pg_dump with a tested restore | ⚪ |

---

### D6.1 – Scheduler
**Outcome:** All jobs run on the IST schedule, skip holidays and catch up after downtime.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | All jobs run on the IST schedule, skip holidays and catch up after downtime | Job runs table over 5 trading days | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D6.2 – EOD report
**Outcome:** Daily report with plan P/L, accuracy and calibration.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Daily report with plan P/L, accuracy and calibration | Report page; sample day | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D6.3 – Monitoring
**Outcome:** Health checks, job failure alerts, provider health, Grafana dashboards.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Health checks, job failure alerts, provider health, Grafana dashboards | Alert test | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D6.4 – Backups
**Outcome:** Nightly pg_dump with a tested restore.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Nightly pg_dump with a tested restore | Restore drill | ⬜ |

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
