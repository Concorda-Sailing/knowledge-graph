---
node_id: concorda-test::tests/dashboard/cross-context-crew.spec.ts::test@114
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 233f5c435859715875402b73b6c3a4537c5c12e985259bc3837fb1e5aeb7dc78
status: current
---

# crew member sees one schedule card with logistics, and detail page shows Sailing with

## Purpose

This test validates the cross-context interaction between a boat owner (Bob) and a crew member (Alice). It ensures that when a user is added to a crew pool and an invite is sent, the event correctly appears in the recipient's schedule with the appropriate logistics and "Sailing with" detail view. It specifically tests the visibility of event-specific details (like notes and departure locations) in the dashboard UI after a user accepts an invite.

## Invariants

- **Idempotency is required** — The test uses `api.createSailingEvent` and `api.setEventCrewPool` with logic to check for existing records first to prevent duplicate seeding during Playwright retries.
- **Identity switching** — The test relies on switching the `ApiClient` token between `bobToken` (owner) and `aliceToken` (crew) to simulate the two-party flow.
- **Navigation-based state** — The test uses `page.goto('/members?tab=schedule')` to ensure the UI state is driven by URL parameters rather than just internal component state.
- **Selector specificity** — Assertions target the `tab` role and specific text content to ensure the correct view is active.

## Gotchas

- **Duplicate card bug** — Per commit `822e3a8`, a previous bug caused two cards to appear (one rich, one blank) due to a duplicate personal-category Event; the test now uses `.first()` and specific text matching to avoid brittle failures.
- **Event lookup requirement** — Per commit `bd0c904`, the test must use `/api/events/personal` for fixture lookup because `createSailingEvent` does not enforce name/date uniqueness, making the lookup necessary for idempotency.
- **Selector fragility** — Per commit `a7e8bd7`, the test must target the `Card` root rather than an anchor to avoid issues with the `onClick` wrapper used in the dashboard.

## Cross-cutting concerns

- **Auth**: Uses `api.login` for two distinct users (Bob and Alice) and manually sets `localStorage.setItem('auth_token', ...)` to drive the browser session.
- **Side effects**: Mutates the personal event feed via `api.createSailingEvent` and `api.upsertSailingEvent`, which affects the visibility of the "My Schedule" tab for the invited user.

## External consumers

None known.
