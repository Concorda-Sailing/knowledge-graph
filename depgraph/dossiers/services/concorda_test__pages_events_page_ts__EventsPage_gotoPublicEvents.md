---
node_id: concorda-test::pages/events.page.ts::EventsPage.gotoPublicEvents
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f8b087607e8f098577743f439c3d6cfe99f7dcfb6c268476f341e29c4bd3e18e
status: current
---

# EventsPage.gotoPublicEvents

## Purpose
Playwright Page Object Model navigation helper that opens the public events listing page (`/events`) and waits for the network to settle. Centralizes the URL shape so specs don't hard-code paths and so a future route change touches one line. Three specs in `tests/events/browse-events.spec.ts` call it as setup before asserting on the unauthenticated browse-events flow: the basic "page loads" smoke check, the "seeded events visible" accordion-expand check, and the "event card shows date and location" check. Sibling to `gotoMemberEvents` (`/members/events`, the authenticated variant), `gotoEvent` (detail by slug), and `gotoSchedule` on the same page object.

## Invariants
- The path stays `/events` — the public listing route. The `/members/events` variant is a separate method (`gotoMemberEvents`); don't merge them. Public vs. member listing is a meaningful distinction in the app (auth gating, different data shape).
- No parameters. If filtering ever needs to be expressed in the URL (query string for category, date range), add a second method or an options arg rather than changing this signature — all three callers expect a bare nav.
- Must leave the page in a state where the listing locators (`eventCards`, `searchInput`) resolve. The two callers that expand month accordions rely on the listing being fully rendered before clicking the month header.
- Symmetric with the other three `goto*` methods on this page object — same two-line shape, same `networkidle` wait. Keep them parallel.

## Gotchas
- `networkidle` is flaky on pages with websocket/SSE traffic or background polling. The suite hasn't had its first live run yet (per the E2E framework memory), so if the events listing grows a live channel (new-event notifications, registration counts on cards), this will hang until the 30s default timeout. Switch to `await this.eventCards.first().waitFor()` at the first sign of trouble.
- The listing groups events by month in an accordion (collapsed by default). After `gotoPublicEvents()`, two of the three callers must click a month header (`/july 2026/i`) before event content is visible. Don't try to assert on event names without expanding first — the smoke test gets away with it only because its regex `/summer series|fall regatta|event/i` matches the month header text too.
- Caller responsibility: the seeded events (Summer Series, July 2026, Boston Harbor location) are seed-data assumptions. If the seed dataset shifts months or names, all three callers break downstream, not this method.

## Cross-cutting concerns
- Auth: none required — `/events` is public. This is the only `EventsPage` `goto*` method explicitly designed for the unauthenticated path; callers should not pre-establish auth fixtures expecting them to matter here.
- Side effects: pure navigation, no DB writes. Safe to call repeatedly.
- Test isolation: navigating mid-test discards in-page state (expanded accordion sections, search input). Don't call from inside a filter/search assertion.

## External consumers
None outside the `concorda-test` repo. Page Object Methods are test-only; the production app does not import from `pages/`.

## Open questions
- Should the four `goto*` methods share a private `_goto(path)` helper? Two-line duplication is fine today; revisit if the wait strategy needs to change in one place or if a fifth route appears.
- Once the suite has its first live run, confirm `networkidle` actually settles on the public listing route — the accordion-rendering pattern suggests the page may make follow-up requests as months expand, but the initial load should be quiet. Verify before encoding timing assumptions into specs.
