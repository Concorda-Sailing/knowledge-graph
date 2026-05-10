---
node_id: concorda-test::tests/boats/schedule-crew-badge-ui.spec.ts::test@157
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 44c8b405693c43b5b2854278bb51526b75cd117c08422b79f82a0f9fc50bc2b3
status: current
---

# crew bookmark → Crew pill DOES render (regression guard)

## Purpose

Verifies that the "Crew pill" (the UI indicator for a user crewing on someone else's boat) correctly renders when a user is added to a schedule as a crew member rather than a captain. This test ensures that the UI correctly reflects the user's status when they lack a `boat_uuid` for a specific regatta.

## Invariants

- **Requires a clean state transition**: To test the "crew" state, the user must first have their existing captain/schedule event removed, as `addRegattasToSchedule` only upgrades roles and cannot downgrade them.
- **Relies on specific DOM attributes**: The test asserts the presence of a button with a `title` containing the string `"crewing on someone else"`.
- **Navigation is required for state refresh**: The test must navigate to `/members?tab=schedule` and wait for `networkidle` to ensure the frontend re-fetches the updated schedule state after the backend change.

## Gotchas

- **Role upgrade/downgrade asymmetry**: Per the logic in the test body, `addRegattasToSchedule` upgrades crew to captain but does not support the reverse. This necessitates the manual removal of the `regattaEventId` via `bob.removeScheduleEvent` to prevent the test from failing due to a stale captain role.
- **Regression Guard**: This test was specifically added/updated to guard against the UI failing to show the crew status when a user is added as crew (see commit `c70d95d`).

## Cross-cutting concerns

- **Auth**: Uses the `bob` user instance (likely a pre-authenticated Playwright fixture).
- **Side effects**: Affects the visibility of the "Crew pill" on the member schedule page.

## External consumers

None known.
