---
node_id: concorda-test::pages/events.page.ts::EventsPage.gotoEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 470af9351e635c8c7203b43632da8fe84f53f448aad6af2585a8e5896be4484e
status: current
---

# EventsPage.gotoEvent

## Purpose
Playwright Page Object Model navigation helper that opens the schedule/event detail page for a specific event by slug (`/events/{slug}`) and waits for the network to settle. Centralizes the URL shape so specs don't hard-code paths and so a future route change touches one line. Four specs use it as setup before asserting on event-level UI: three in `tests/events/event-registration.spec.ts` (registration flow start, ticket selection, confirmation) and one in `tests/events/browse-events.spec.ts` (detail-from-listing check). Sibling to `gotoPublicEvents`, `gotoMemberEvents`, and `gotoSchedule` on the same page object.

## Invariants
- The path stays `/events/{slug}` — public-events route, not under `/members/`. The detail page is intentionally reachable without auth; specs that need member context navigate after auth setup.
- Parameter is a slug (string), not a numeric id. All current callers pass `'summer-series-2026'`. If the route ever accepts numeric ids, keep slug as the primary call signature — readability in spec output depends on it.
- Must leave the page in a state where the locators declared on `EventsPage` (registerButton, ticketSelector, addToScheduleButton, etc.) resolve. Don't drop `waitForLoadState('networkidle')` without substituting a locator-based wait.
- Symmetric with the other three `goto*` methods on this page object — same two-line shape, same wait. Keep them parallel.

## Gotchas
- `networkidle` is flaky on pages with websocket/SSE traffic. The suite hasn't had its first live run yet (per the E2E framework memory), so if the event detail page grows a live channel (registration count, presence), this will hang until the 30s default timeout. Switch to `await this.registerButton.waitFor()` (or another stable detail-page locator) at the first sign of trouble.
- Caller responsibility: the `summer-series-2026` slug is a seed-data assumption. Specs depend on the seeded event existing; if the seed is renamed, all four callers break, not this method.
- No 404 handling. If the slug doesn't resolve, the test fails downstream on the first locator wait, not here — diagnosis points at the assertion rather than the navigation.

## Cross-cutting concerns
- Auth: none required by this method — `/events/{slug}` is public. Specs that go on to register or add-to-schedule must have auth set up separately by their fixture.
- Side effects: pure navigation, no DB writes. Safe to call repeatedly within a test.
- Test isolation: navigating mid-test discards in-page state (open ticket selector, unsaved quantity). Don't call from inside an in-progress registration flow.

## External consumers
None outside the `concorda-test` repo. Page Object Methods are test-only; the production app does not import from `pages/`.

## Open questions
- Should the four `goto*` methods on `EventsPage` share a private `_goto(path)` helper? Two-line duplication is fine today; revisit if the wait strategy needs to change in one place or if a fifth route appears.
- Once the suite has its first live run, confirm `networkidle` actually settles on the event detail route — if not, switch to a locator-based wait before flake gets encoded into spec timing expectations.
