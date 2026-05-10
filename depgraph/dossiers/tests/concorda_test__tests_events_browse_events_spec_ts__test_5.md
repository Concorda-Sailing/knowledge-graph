---
node_id: concorda-test::tests/events/browse-events.spec.ts::test@5
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85bd0223e50a31bab8599524f690986c0b3386c57285eed594392227ce9fef24
status: current
---

# public events page loads

## Purpose

Verifies the visibility and accessibility of the public and member-only event views. It ensures that the `EventsPage` correctly navigates to public event lists, expands month accordions to reveal event details, and validates that the member-specific view is protected by authentication.

## Invariants

- **Public access is unauthenticated.** The `gotoPublicEvents()` call must work without an active session or token.
- **Month accordions are interactive.** Tests rely on clicking a `monthHeader` (e.g., "July 2026") to reveal the underlying event cards.
- **Seeded data is required.** The test expects specific text patterns like "Summer Series" and "Boston Harbor" to be present in the DOM to pass.
- **URL redirection.** The `memberEvents` view must resolve to `/members/events/` and should not redirect to a login page if the session is valid.

## Gotchas

- **Selector fragility.** Per commit `f552929`, selectors must be aligned with the actual UI; recent changes were required to fix the setup for the first green run.
- **Accordion-dependent visibility.** Events are nested within month accordions; if the `monthHeader` is not clicked, `expect(summerSeries).toBeVisible()` will fail.
- **Seeded data dependency.** The test is not a generic "empty state" test; it relies on the existence of specific strings (e.g., "july 2026" and "boston harbor") which are provided by the test setup.

## Cross-cutting concerns

- **Auth**: `memberEvents` view requires an authenticated session to avoid redirecting to login.
- **Side effects**: Verifies the visibility of the event card components used in the main dashboard and schedule views.

## External consumers

None known.
