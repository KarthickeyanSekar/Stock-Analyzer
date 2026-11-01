[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Previous phase](phase-05-validation.md) · [Next phase →](phase-05c-whatsapp.md)

# Phase 5b – Users

**Phase outcome:** Other people can sign up with OAuth and an invite code, and each user sees only their own data.
**Status:** 🟡 Built and verified; waiting for your OAuth apps and a legal check before inviting others · **Branch:** `feature/phase5b-users` · **Plan:** [09 – Roadmap](../09-roadmap.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D5b.1 | OAuth sign-in | Google and Microsoft sign-in work (OIDC, PKCE) | 🟡 Built; real Google/Microsoft check needs your OAuth apps |
| D5b.2 | Invite codes | Admins create, share, revoke codes; expiry and max uses enforced | ✅ |
| D5b.3 | Roles & separation | admin / user roles; per-user plans, settings, watchlists | ✅ |
| D5b.4 | Compliance basics | Privacy notice, account deletion, audit log | ✅ |

---

### D5b.1 – OAuth sign-in
**Outcome:** Google and Microsoft sign-in work (OIDC, PKCE).

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | OIDC Authorization Code + PKCE (S256) with state and nonce; ID token signature, issuer, audience, expiry and nonce verified (Q72) | Unit tests with a fake identity provider and signed test tokens | ✅ 2026-11-01: `infrastructure/auth/oidc.py`; `test_oidc.py` (forged signature, wrong aud / iss / nonce, expired, unverified email, Microsoft tenant issuer) |
| 2 | Google and Microsoft configured from `.env` (client ID/secret); a provider without credentials is hidden on the sign-in page | e2e test | ✅ 2026-11-01: providers only with client id + secret; `/api/auth/options`; sign-in page buttons |
| 3 | Session cookie: HttpOnly, SameSite=Lax, Secure in prod, 7-day sliding expiry; only the token hash stored (Q71); sign-out | Unit + e2e tests | ✅ 2026-11-01: `test_session_cookie_is_http_only_and_lax`; token hash only (DB test) |
| 4 | Dev-only sign-in for local work (`SA_DEV_LOGIN=true`), refused when `SA_ENV=prod` | Unit test | ✅ 2026-11-01: `test_dev_login_is_never_on_in_prod` |
| 5 | Real Google / Microsoft sign-in checked by you after registering the OAuth apps | Manual check (needs your client IDs) | ⬜ Needs your OAuth client IDs (Google Cloud + Microsoft Entra) |

---

### D5b.2 – Invite codes
**Outcome:** Admins create, share, revoke codes; expiry and max uses enforced.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Admins create codes (`SA-XXXX-XXXX`, default 1 use, 7 days, role user), list and revoke them | e2e tests | ✅ 2026-11-01: `test_sign_up_needs_a_valid_invite`; `auth.e2e.mjs` |
| 2 | Sign-up needs a valid code (exists, not expired, uses left, not revoked); otherwise a clear message and no account | Unit tests per rule | ✅ 2026-11-01: `test_users.py` + API test (missing, unknown, used, revoked, expired) |
| 3 | Emails in `SA_ADMIN_EMAILS` become admin on first sign-in without a code | Unit test | ✅ 2026-11-01: `test_full_flow_state_is_single_use_and_expires`, API tests |

---

### D5b.3 – Roles & separation
**Outcome:** admin / user roles; per-user plans, settings, watchlists.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Every API except health and sign-in requires a session (401); admin APIs require the admin role (403) | e2e tests | ✅ 2026-11-01: `test_everything_needs_a_session`; 403 for users on admin APIs |
| 2 | Journal plans and settings belong to a user; each user sees only their own (Q73: the first admin claims existing ones) | e2e test with two users; migration | ✅ 2026-11-01: `test_users_only_see_their_own_plans`, `test_first_admin_claims_plans_from_before_accounts`; migration 0007 |
| 3 | Watchlist per user (add / remove / list) with a star on the stock page | e2e test + Playwright | ✅ 2026-11-01: `test_watchlist`; star in `auth.e2e.mjs` |
| 4 | Admin › Users: list users, disable / enable; a disabled user can't sign in or use a session | e2e test | ✅ 2026-11-01: `test_disabled_users_are_signed_out_and_refused` |

---

### D5b.4 – Compliance basics
**Outcome:** Privacy notice, account deletion, audit log.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Privacy notice page (what is stored, why, deletion) | Playwright | ✅ 2026-11-01: `/privacy`; `auth.e2e.mjs` |
| 2 | Delete my account: removes the user, their plans, settings, watchlist and sessions | e2e test | ✅ 2026-11-01: `test_delete_account_removes_everything`; DB cascade test; `auth.e2e.mjs` |
| 3 | Audit log of sign-ins, sign-ups, invite actions, role changes and deletions | e2e test | ✅ 2026-11-01: API + DB tests; Admin › Users audit card |

---

## Before inviting anyone (doc 19 "What changes with other users")
- Market-data licence: personal API plans usually forbid showing prices to others (redistribution).
- SEBI: "hold N days → X%" for others can need Research Analyst registration; keep it free, invite-only, educational.
- DPDP Act 2023: the privacy notice and account deletion are in place; keep data to email + name.

## Phase exit criteria
- [ ] All deliverables ✅
- [x] `make lint` and `make test` pass in containers
- [x] Docs and Open Questions updated
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Built: OIDC + PKCE, sessions, invites, roles, per-user data, watchlist, privacy, deletion, audit | Others can join once OAuth apps exist |
| 2026-11-01 | Phase planned: detailed criteria; Q71–Q73 decided | Phase 5b started |
| 2026-10-31 | Outcomes drafted | Deliverables folder created |
