[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-02-trade-journal.md) · [Next phase →](phase-04-screener.md)

# Phase 3 – Long-Term Engine

**Phase outcome:** ML predictions per holding category, with calibrated ranges and target probabilities, beat the baseline models.
**Status:** ⚪ Not started · **Branch:** _when started_ · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D3.1 | Data points | The researched data points (doc 21) are computed for every stock and date | ⚪ |
| D3.2 | Feature store & labels | Point-in-time features and triple-barrier labels are stored and versioned | ⚪ |
| D3.3 | Models per category | LightGBM quantile + target-probability models trained for 50D … 3Y | ⚪ |
| D3.4 | Calibration | 80% ranges contain 75–85% of outcomes; calibration error ≤ 5 pp | ⚪ |
| D3.5 | Quality gates & registry | Only models that pass the gates become ACTIVE; rollback works | ⚪ |

---

### D3.1 – Data points
**Outcome:** The researched data points (doc 21) are computed for every stock and date.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | The researched data points (doc 21) are computed for every stock and date | Unit tests per calculator; research tracker ✅ | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D3.2 – Feature store & labels
**Outcome:** Point-in-time features and triple-barrier labels are stored and versioned.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Point-in-time features and triple-barrier labels are stored and versioned | Leakage tests pass | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D3.3 – Models per category
**Outcome:** LightGBM quantile + target-probability models trained for 50D … 3Y.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | LightGBM quantile + target-probability models trained for 50D … 3Y | MLflow runs; metrics recorded | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D3.4 – Calibration
**Outcome:** 80% ranges contain 75–85% of outcomes; calibration error ≤ 5 pp.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | 80% ranges contain 75–85% of outcomes; calibration error ≤ 5 pp | Walk-forward evaluation report | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D3.5 – Quality gates & registry
**Outcome:** Only models that pass the gates become ACTIVE; rollback works.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Only models that pass the gates become ACTIVE; rollback works | Registry test; gate report | ⬜ |

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
