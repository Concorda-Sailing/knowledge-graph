---
node_id: concorda-test::tests/events/browse-events.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 53422ecd090997e99fc56a1653f12834549dedfb1162d0656cdbede13ba7d94d
status: llm_drafted
---

# seeded events are visible

## Purpose

Verifies the visibility and accessibility of event data on both public and member-only views. It ensures that the `EventsPage` helper correctly navigates to the public events list, expands month accordions to reveal seeded events (like "Summer Series"), and validates that the event detail page loads with the correct content.

## Invariants

- **Public access is unauthenticated.** The `public events page loads` test must pass without any login setup to ensure the landing page is accessible to non-members.
- **Month accordions are required for visibility.** Events are nested within month-based UI components; the test must explicitly click a `monthHeader` (e.g., "July 2026") to make the event cards visible to the Playwright locator.
- **URL structure for members.** The `member events page loads when authenticated` test expects a specific path (`/members/events`) and validates that the user is not redirected to a login page.

## Gotchas

- **Selector fragility.** Per commit `f552929`, selectors must be aligned with the actual UI to avoid failures. Tests rely on regex matches (e.g., `/july 2026/i`) which are sensitive to the exact text rendered by the `formatInOrgTz` helper used in the frontend.
- **Timeout sensitivity.** The `summer series` visibility check uses a `10_000` ms timeout, whereas accordion expansion checks use `5_000` ms. If the seeded data or the month-header click fails, the subsequent event visibility check will fail.

## Cross-cutting concerns

- **Auth**: `member events page loads when authenticated` requires a valid session to prevent a redirect to the login page.
- **Side effects**: Verifies the visibility of seeded event data (e.g., "Summer Series", "Boston Harbor") which is used to validate the `EventsPage` rendering logic.

## External consumers

None known.
