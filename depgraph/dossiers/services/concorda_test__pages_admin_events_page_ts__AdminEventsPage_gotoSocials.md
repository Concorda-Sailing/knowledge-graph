---
node_id: concorda-test::pages/admin/events.page.ts::AdminEventsPage.gotoSocials
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0e4b4b9b1b203469677e5e43383254958528c1bd7fa9aa1d836fd4eaf411d85a
status: current
---

# AdminEventsPage.gotoSocials

## Purpose
Playwright Page Object Model navigation helper that lands the test browser on the admin Socials sub-tab (`/members/admin/events/socials`) and waits for the network to settle. It exists so specs that exercise admin social-event CRUD don't repeat the URL or the load-wait dance, and so the URL/selector can be updated in one place if the admin events area is restructured. Six specs in `tests/admin/event-management.spec.ts` use it as setup before asserting on the social-events table or driving the Add/Edit dialogs declared on this page object.

## Invariants
- The path stays `/members/admin/events/socials` — the route is the source of truth for callers; if the web app moves it, change here, not in specs.
- The method must leave the page in a state where the locators declared on `AdminEventsPage` (eventTable, addEventButton, dialog inputs, toast) resolve. Don't refactor away the `waitForLoadState('networkidle')` without a stronger wait substitute, or specs will race the table render.
- Symmetric with `gotoRaces` / `gotoSeries`: same shape, same wait. Keep them parallel — divergence makes the page object harder to reason about.
- Uses `page.goto`, not a tab click. This deliberately bypasses `socialsTab` so the method works regardless of which sub-page the test starts on.

## Gotchas
- `networkidle` is known-flaky on pages with long-poll or websocket traffic. The suite hasn't been run live yet (per the project memory: "E2E test framework — needs first live run"), so if the admin events page grows a websocket/SSE channel, this wait will hang until the 30s default timeout. Swap to a locator-based wait (`await this.eventTable.waitFor()`) at the first sign of trouble.
- The file has exactly one commit (`fd0c570` initial scaffolding). No revert history to mine — treat behavior as unverified against the live app.
- The admin route is gated by org_admin role; an unauthenticated or under-privileged session will land on a redirect and `eventTable` will not appear. Auth setup is the spec's responsibility, not this method's.

## Cross-cutting concerns
- Auth: requires an admin-role session in browser context (cookie/JWT established by the spec's auth fixture). This method does not establish auth.
- Side effects: pure navigation — no DB writes, no API mutations. Safe to call repeatedly within a test.
- Test isolation: navigating mid-test discards in-page state (open dialogs, unsaved form input). Don't call from inside a flow that has a dialog open.

## External consumers
None outside the `concorda-test` repo. Page Object Methods are test-only; the production app does not import from `pages/`.

## Open questions
- Should the three `goto*` methods share a private `_goto(path)` helper? Three-line duplication is fine today; revisit if a fourth tab appears or if the wait strategy needs to change in one place.
- Once the suite has its first live run, confirm `networkidle` actually settles on this route — if not, switch to a locator wait before the flake is encoded into spec expectations.
