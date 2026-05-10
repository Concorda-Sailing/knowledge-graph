---
node_id: concorda-api::schemas/event_crew.py::EventCrewAssign
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 61ba52663a5511fe41a8070096ddf11b1b99b83655c5f7a51e259540fa7dfa6b
status: llm_drafted
---

# EventCrewAssign

## Purpose

The schema for assigning a specific person to a position within an event's crew. It is used to transition a person from a "pool member" or "invitee" status into a concrete role. Unlike `EventCrewRespond`, which handles the user's choice to accept/decline, this model is the structural contract for the administrative or automated assignment of a `person_uuid` to a `position_name`.

## Invariants

- **`person_uuid` is required.** The assignment must target a specific, valid person identifier.
- **`position_name` is optional.** Passing `None` acts as an unassign command, removing the person from their current role.
- **Strictly for assignment/unassignment.** This is a structural model for the `PUT /api/events/{id}/sailing-event/crew-assign` endpoint.

## Gotchas

- **Role transitions rely on `EventCrewStatus` enum.** Per commit `dd72f2f`, the route logic now writes through the `EventCrewStatus` enum; ensure any logic using this schema respects the state machine transitions of the crew member.
- **Skipper override capability.** Per commit `4e00a7d`, the system allows a skipper to act on behalf of a crew member (e.g., marking an invite accepted/declined); this schema is the payload used when the skipper is performing these administrative actions.

## Cross-cutting concerns

- **Auth**: Requires appropriate permissions (typically Skipper or Admin) to execute the assignment via the event router.
- **Side effects**: Changes to crew assignments via this schema trigger updates to the event's roster visibility and potentially the `resume_published` flag status (see `3927ca0`).

## External consumers

- `PUT /api/events/{id}/sailing-event/crew-assign` (via `routers/events.py`)
