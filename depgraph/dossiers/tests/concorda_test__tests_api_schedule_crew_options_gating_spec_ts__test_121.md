---
node_id: concorda-test::tests/api/schedule-crew-options-gating.spec.ts::test@121
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 48956be1df2d52db7ee97e377559e975d69d5acae1c0e1c43f48f3a587dc9b9d
status: llm_drafted
---

# captain-mode bookmark hides crew_boats

## Purpose

This test verifies the "Captain Mode" logic for schedule items, specifically ensuring that a user's primary role as a captain suppresses certain "crew" indicators. It asserts that when a user is captaining their own boat for a regatta, the `viewer_role` is null and the `crew_boats` list is empty, even if they are also part of another user's `event_crew` pool. This prevents the UI from incorrectly displaying a "Crew" badge when the user's primary commitment is a captaincy.

## Invariants

- **Captaincy takes precedence.** If a user has a `SailingEvent` (captain role) for the same regatta, the `viewer_role` must be `null` and `crew_boats` must be an empty array `[]`.
- **`viewer_role` is null in captain mode.** The test explicitly expects `item?.viewer_role ?? null` to be `null` to ensure the "Crew" badge is suppressed.
- **Manual cleanup is required.** The test relies on `removeScheduleEvent` to clear existing bookmarks/rows before setting up the captain state, as `addRegattasToSchedule` does not automatically downgrade a user from a crew role to a captain role.

## Gotchas

- **The "Crew Badge" bug.** Per commit `379fbcc`, previously, having an active `EventCrew` row tied to a peer's `SailingEvent` would unconditionally set the `viewer_role` to "crew," causing a misleading "Crew" badge to appear on the user's schedule card even if they were the captain of their own boat.
- **Stateful setup dependency.** The test requires a specific sequence: a user must be a "crew" member (via `setEventCrewPool` and `sendEventCrewInvites`) and then must be "upgraded" to a captain (via `addRegattasToSchedule`) to verify the suppression logic works.
- **`addRegattasToSchedule` is not a downgrade.** As noted in the source, this method does not downgrade a user from `crew` to `captain`; the test must manually call `removeScheduleEvent` to ensure a clean state transition.

## Cross-cutting concerns

- **Auth**: Uses `bob` and `dan` (ApiClient instances) to simulate different user roles and interactions.
- **Side effects**: Directly tests the logic that governs the rendering of the "Crew" pill/badge on the schedule detail card in the UI.

## External consumers

None known.
