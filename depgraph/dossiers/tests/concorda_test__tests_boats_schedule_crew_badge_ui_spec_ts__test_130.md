---
node_id: concorda-test::tests/boats/schedule-crew-badge-ui.spec.ts::test@130
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d5edee31d1a6b691b59b111c2273d272360d4298918d3df5ce1bfba1f832db82
status: current
---

# captain w/ peer EventCrew → no Crew pill, no request-to-crew avatars

## Purpose

Verifies the visibility logic for the "Crew" UI elements on the member schedule page. Specifically, it ensures that when a user is the captain of their own boat (EventCrew), the "Crew" pill and "request to crew" avatars are hidden, and that these elements reappear correctly when the user is added as a crew member via a bookmark.

## Invariants

- **Uses `cardLocator` for scoping**: All assertions must be scoped to the specific regatta card to avoid false positives from other elements on the page.
- **Relies on `storageState`**: The test assumes the browser is already authenticated as "Bob" (the boat-owner project) to bypass the login flow.
- **Targeting via `title` attribute**: The test asserts against the `title` attribute (e.g., `[title*="crewing on someone else"]`) rather than raw text to remain resilient to visual chrome changes in `schedule-card.tsx`.

## Gotchas

- **Manual state cleanup required**: Per the logic in the regression guard, `addRegattasToSchedule` only upgrades from crew to captain, but never the inverse. To test the "Crew" state, the existing schedule event must be explicitly removed via `bob.removeScheduleEvent` first.
- **Regression Guard**: This test was added/updated in commit `c70d95d` to ensure the Crew badge is correctly gated when a user is a captain.

## Cross-cutting concerns

- **Auth**: Uses pre-authenticated `storageState` for the "Bob" user.
- **Side effects**: Verifies the UI state of the `schedule-card.tsx` component, specifically the visibility of the Crew pill and request-to-crew buttons.

## External consumers

None known.
