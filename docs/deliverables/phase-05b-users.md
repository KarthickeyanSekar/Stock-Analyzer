[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-05-validation.md) · [Next phase →](phase-05c-whatsapp.md)

# Phase 5b – Users

**Phase outcome:** Other people can sign up with OAuth and an invite code, and each user sees only their own data.
**Status:** ⚪ Not started · **Branch:** _when started_ · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D5b.1 | OAuth sign-in | Google and Microsoft sign-in work (OIDC, PKCE) | ⚪ |
| D5b.2 | Invite codes | Admins create, share, revoke codes; expiry and max uses enforced | ⚪ |
| D5b.3 | Roles & separation | admin / user roles; per-user plans, settings, watchlists | ⚪ |
| D5b.4 | Compliance basics | Privacy notice, account deletion, audit log | ⚪ |

---

### D5b.1 – OAuth sign-in
**Outcome:** Google and Microsoft sign-in work (OIDC, PKCE).

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Google and Microsoft sign-in work (OIDC, PKCE) | e2e test; manual check | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D5b.2 – Invite codes
**Outcome:** Admins create, share, revoke codes; expiry and max uses enforced.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Admins create, share, revoke codes; expiry and max uses enforced | Unit + e2e tests | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D5b.3 – Roles & separation
**Outcome:** admin / user roles; per-user plans, settings, watchlists.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | admin / user roles; per-user plans, settings, watchlists | Authorization tests | ⬜ |

_Detailed criteria are added when the phase is planned._

---

### D5b.4 – Compliance basics
**Outcome:** Privacy notice, account deletion, audit log.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Privacy notice, account deletion, audit log | Checklist | ⬜ |

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
