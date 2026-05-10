---
node_id: concorda-api::schemas/event_crew.py::EventCrewRespond
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4e2b85124068b1992ebf5e718614a18d5521c0e7b0f73438a0653b5e203d5c69
status: llm_drafted
---

# EventCrewRespond

## Purpose

The schema for a user's response to a crew invitation. It captures the intent of a person (accept or decline) and allows for optional self-selection of a specific position. Use this when implementing endpoints that handle the transition from an "invited" state to a "confirmed" or "declined" state in the event roster.

## Invariants

- **`action` is required and must be a string.** It typically holds the values `"accept"` or `"decline"`.
- **`position_name` is optional.** It is used for self-selection during the acceptance flow; if `None`, the user is not claiming a specific role.
- **Strictly for response actions.** This is a payload for a user's decision, distinct from `EventCrewAssign` which is used for administrative assignments.

## Gotchas

- **Action value dependency.** Per commit `dd72f2f`, the route logic relies on the `action` string to drive the `EventCrewStatus` enum. If the string values in the API implementation change, this schema will no longer correctly drive the state machine.
- **Role selection ambiguity.** While `position_name` is optional, the backend logic expects it to be provided if the user is attempting to claim a specific role during the `accept` action.

## Cross-cutting concerns

- **Auth**: Requires a valid session/token to ensure the user is responding to an invitation they are actually part of.
- **Side effects**: Successful responses trigger updates to the event crew roster, which may affect the visibility of the crew list in the UI.

## External consumers

- `PUT /api/events/{0}/sailing-event/crew-respond` (Directly consumes this schema for the request body).
