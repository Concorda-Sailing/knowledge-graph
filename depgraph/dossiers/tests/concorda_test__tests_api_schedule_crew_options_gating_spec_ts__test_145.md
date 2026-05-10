---
node_id: concorda-test::tests/api/schedule-crew-options-gating.spec.ts::test@145
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bec270d0d8c89b450867dcc59601a0b00e4a6312b902e2be79a4cd37ed1c145b
status: llm_drafted
---

# captain with peer-boat EventCrew row keeps Crew badge off

## Purpose

Verifies that a user's primary commitment (Captaincy) takes precedence over secondary roles (Crew) in the schedule view. Specifically, it ensures that if a user is captaining their own boat for a regatta, the `viewer_role` does not flip to "crew" even if they are also part of an `EventCrew` pool for a peer's boat in the same event. This prevents the "Crew" badge from appearing on a user's schedule card when they are actually the primary captain.

## Invariants

- **Captaincy suppression**: If a user has a `SailingEvent` with a `boat_uuid` for the current regatta, `item.viewer_role` must be `null` (or not "crew").
- **Boat identity preservation**: The `item.sailing_event.boat_uuid` must reflect the user's own boat, not the peer's boat, even when an `EventCrew` row exists.
- **State dependency**: The test relies on `addRegattasToSchedule` to establish the captain role, as this method does not automatically downgrade a user from captain to crew.

## Gotchas

- **The "Crew Badge" Bug**: Previously, `external_crew_event_ids` caused the `viewer_role` to be unconditionally set to "crew" if any active `EventCrew` row existed. Per commit `379fbcc`, the fix ensures that captaining one's own boat suppresses this badge.
- **Order of operations**: `addRegattasToSchedule` is an additive/upgrade operation. To test a "crew-only" state, the test must explicitly call `removeScheduleEvent` first to clear any existing captain-mode bookmarks, otherwise the user remains in captain mode.
- **Selection fragility**: The test guards against a bug where the schedule card might surface a peer's boat name/time instead of the user's own. This is a defense against `.first()` being used without an explicit `order_by` in the underlying API.

## Cross-cutting concerns

- **Auth**: Uses `bob` and `dan` identities to simulate owner-level actions (setting the crew pool) vs. viewer-level visibility.
- **Side effects**: Validates the logic used by the schedule card to render the "Crew" pill/badge and the `viewer_role` string.

## External consumers

None known.
