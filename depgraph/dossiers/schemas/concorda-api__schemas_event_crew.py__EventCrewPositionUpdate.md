---
node_id: concorda-api::schemas/event_crew.py::EventCrewPositionUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 24b605696b56d73439e94dd6d233b544846bd045728cc3f1ae1c2e6768848930
status: current
---

# EventCrewPositionUpdate

## Purpose

Defines the schema for updating a person's specific role within an event's crew roster. It is used to transition a user from an unassigned state to a specific position or to unassign them by setting the position to null. This is distinct from `EventCrewMarkResponse`, which handles the binary acceptance/decline of an invite.

## Invariants

- **`position_name` is optional.** Setting this field to `None` (null) is the explicit mechanism to unassign a user from their current role.
- **Used by `PUT /api/events/{0}/sailing-event/crew-position`.** This endpoint relies on this schema to process role changes.

## Gotchas

- **Role transitions are driven by the `EventCrewStatus` enum.** Per commit `dd72f2f`, route writes for crew positions now flow through this status logic to ensure state consistency.
- **Skipper override capability.** Per commit `4e00a7d`, the logic surrounding crew updates allows a skipper to mark an invite as accepted or declined on a crew member's behalf, which may affect how `position_name` is validated or processed in the service layer.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to the event router.
- **Side effects**: Updates to crew positions affect the event's roster state and potentially the visibility of crew members in the event dashboard.

## External consumers

- Web UI (Event Crew Roster management).
