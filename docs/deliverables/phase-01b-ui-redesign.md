[🏠 Docs index](../README.md) · [🎯 Deliverables](README.md) · [← Phase 1](phase-01-foundation-poc.md) · [Next phase →](phase-02-trade-journal.md)

# Phase 1b – UI/UX Redesign

**Phase outcome:** the POC flow (discover → analyse → plan → track → close → review) feels like a finished, professional
finance tool: one consistent design system in light and dark, predictions shown as clear visuals, and every action giving
clear feedback. Approved by you on mockups **before** it is built.

**Status:** 🟡 Built, awaiting your review · **Branch:** `feature/ui-redesign-plan` (plan), then one branch per slice · **Plan:** [28 – UI/UX Redesign Plan (End to End) 🎨](../28-ui-ux-redesign-plan.md)

## Deliverables
| ID | Deliverable | Outcome (what is true when done) | Status |
|---|---|---|---|
| D1b.0 | Input + mockups | Clickable mockups of every screen (light + dark) approved by you | 🟡 |
| D1b.1 | Design system | Every colour, size and icon comes from tokens/Lucide; light and dark both work | ✅ |
| D1b.2 | App shell | Sidebar, top bar with ⌘K search, market status and data badge on every page | 🟡 |
| D1b.3 | Stock detail | Predictions readable at a glance as range bars with exact numbers | ✅ |
| D1b.4 | Plan & close flows | Start a plan in a guided sheet; close in a dialog that previews the outcome | 🟡 |
| D1b.5 | Stocks, Journal, Home, Providers | Every screen matches its approved mockup | ✅ |
| D1b.6 | States, a11y, responsive | Loading, empty and error states everywhere; AA accessible; works on phones | 🟡 |

---

### D1b.0 – Input + mockups
**Outcome:** we agree what the UI should look like before code changes.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Q58–Q62 answered (pain points, references, theme, phone, process) | Decision log | ✅ 2026-11-01: Kite-like, modern, animated, responsive; system theme + toggle; build in code |
| 2 | Mockups for Home, Stocks, Stock detail, Start-plan sheet, Journal (3 tabs), Close dialog, Providers, in light + dark | Shared mockup link | 🟡 Direction mockups for Stock detail + Home on the design canvas; you chose to build the rest in code (Q62) |
| 3 | Mockups use the real synthetic numbers (not lorem ipsum) | Review | ✅ 2026-11-01 |
| 4 | Your approval recorded | Sign-off row below | ⬜ Your review of the built UI (replaces mockup approval) |

### D1b.1 – Design system
**Outcome:** one visual system; no ad-hoc styling.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | No `slate-*`, raw hex or emoji in `app/`, `pages/`, `features/` | Lint rule / grep in `make lint` | ✅ 2026-11-01: `npm run lint` → `UI rules: OK` (was 60 problems) |
| 2 | Semantic tokens `gain`, `loss`, `warning`, `synthetic` added; chart colours read from tokens | Code review | ✅ 2026-11-01: `src/index.css`; chart reads tokens via `useCssVars` |
| 3 | Light + dark themes with a toggle that remembers the choice | Screenshots | ✅ 2026-11-01: next-themes, follows the system; `make ui-shots` dark screenshots |
| 4 | All numbers use `tabular-nums`; gain/loss always shown with sign, not colour only | Code review + screenshots | ✅ 2026-11-01: global `tabular-nums`; arrows/signs on every gain/loss |
| 5 | Missing shadcn components added (Command, Sheet, Dialog, Tooltip, Skeleton, Sonner, Progress, Slider, Select) | `shared/ui` | ✅ 2026-11-01: 22 components in `shared/ui` |

### D1b.2 – App shell
**Outcome:** consistent navigation and context on every page.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Collapsible sidebar with Lucide icons; Home at `/`, status moved to `/status` | Screenshot | ✅ 2026-11-01: sidebar (desktop), bottom nav (phone), `/status` |
| 2 | ⌘K command palette finds any stock and page | Playwright | 🟡 2026-11-01: built (⌘K / Ctrl+K); no automated test yet |
| 3 | Top bar: NSE open/closed + IST time, data badge (SYNTHETIC / provider), theme toggle | Screenshot | ✅ 2026-11-01: live NSE status, SYNTHETIC badge with tooltip, theme toggle |
| 4 | Full keyboard navigation with visible focus | Manual check | ⬜ Manual check pending |

### D1b.3 – Stock detail
**Outcome:** the prediction is the clearest thing on the page.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Header with last close, day change, SYNTHETIC badge, Start plan button | Screenshot | ✅ 2026-11-01: `stock-desktop-light.png` |
| 2 | Themed chart with 1M / 6M / 1Y / 5Y / All, volume, crosshair, plan lines | Screenshot | ✅ 2026-11-01: area + volume, plan lines; locale bug found and fixed via screenshots |
| 3 | Range bar per category (p10–p90, p50 marker, zero line) + median, chance up, chance of target, CAGR 1Y+ | Screenshot + component test | ✅ 2026-11-01: `prediction-ranges.tsx` + `ranges.test.ts` |
| 4 | Target odds bar chart for the selected category | Screenshot | ✅ 2026-11-01: `target-odds.tsx` |

### D1b.4 – Plan & close flows
**Outcome:** starting and closing a plan is guided, fast and unambiguous.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Start-plan sheet: category → target → risk → review, with live target/stop prices, end date, suggested amount | Playwright | ✅ 2026-11-01: `start-plan-sheet-desktop-light.png` |
| 2 | Close dialog with live outcome preview before confirming | Playwright | 🟡 2026-11-01: built; `previewOutcome` unit-tested (mirrors the backend); Playwright flow pending |
| 3 | Toasts on success/failure with a link to the plan | Playwright | ✅ 2026-11-01: Sonner toasts with a Journal action |
| 4 | Plan started in under 30 seconds by a first-time user | Your walkthrough | ⬜ Your walkthrough |

### D1b.5 – Stocks, Journal, Home, Providers
**Outcome:** every remaining screen matches its approved mockup.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Stocks data table: sort, sector filter, 1Y median prediction, chance up | Screenshot | ✅ 2026-11-01: `stocks-desktop-light.png`; cards on phones |
| 2 | Journal tabs: Active (progress bars), Closed (filters), Track record (per-category outcomes) | Screenshot | ✅ 2026-11-01: Active / Closed / Track record |
| 3 | Home: KPIs, active plans with progress, recent outcomes, empty state | Screenshot | ✅ 2026-11-01: `home-desktop-light.png` |
| 4 | Providers as cards with test status and time | Screenshot | ✅ 2026-11-01 |
| 5 | Backend: day change + 1Y return per stock; journal summary endpoint | e2e tests | ✅ 2026-11-01: `/api/stocks/overview`, `/api/trade-plans/summary` + e2e tests |

### D1b.6 – States, accessibility, responsive
**Outcome:** the app is robust and usable for everyone.

| # | Acceptance criterion | How to verify (evidence) | Result |
|---|---|---|---|
| 1 | Skeleton, empty and error states on every screen | Screenshots | ✅ 2026-11-01: `shared/components/data-states.tsx` used on every page |
| 2 | WCAG 2.1 AA contrast in both themes; outcomes not by colour alone | Accessibility review | 🟡 Token pairs chosen for AA; formal accessibility review pending |
| 3 | Phone layout: stacked sections, tables as cards, bottom navigation | Screenshots at 390 px | ✅ 2026-11-01: `*-phone-light.png` (header stacking bug found and fixed) |
| 4 | Playwright visual snapshots (light + dark) for every screen | `make e2e` | 🟡 2026-11-01: `make ui-shots` renders 16 screenshots and fails on page errors; image diffing not yet |

---

## Phase exit criteria
- [ ] D1b.0 – D1b.6 all ✅
- [ ] `make lint` and `make test` pass in containers; Playwright suite passes
- [ ] Your final walkthrough of the demo script on the new UI
- [ ] Merged into `develop` by PR

## Sign-off
| Date | Who | Notes |
|---|---|---|
| | | |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-01 | Redesign built in code (shell, design system, all screens); verified with real-browser screenshots | Q62: build in code |
| 2026-10-31 | Phase 1b defined | POC UI judged unfinished; redesign end to end with a mockup review gate |
