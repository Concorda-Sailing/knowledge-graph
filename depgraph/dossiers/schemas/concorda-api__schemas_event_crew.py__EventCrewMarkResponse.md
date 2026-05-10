---
node_id: concorda-api::schemas/event_crew.py::EventCrewMarkResponse
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e3c3b903d376ede1f9c527da476cc50b9728eb075f63f81a691518e2a98f0bc4
status: llm_drafted
---

# EventCrewMarkResponse

## Purpose

The response schema for marking a crew member's status on a sailing event. It captures the result of an action (accept/decline) taken by a person regarding a specific crew invitation. This is distinct from `EventCrewAssign`, which is used for assigning roles, whereas this is used for the status transition of the invitation itself.

## Invariants

- **`person_uuid` is a required string.** It identifies the specific individual responding to the invite.
- **`action` must be one of two specific strings.** The current implementation expects `"accept"` or `"decline"`.
- **Used by `PUT /api/events/{0}/sailing-event/crew-mark-response`.** This is the primary endpoint that consumes this schema.

## Gotchas

- **Skipper override capability:** Per commit `4e00a7d`, the skipper has the authority to mark an invite as accepted or declined on behalf of the crew member. This means the `person_uuid` in this schema does not strictly represent the person performing the action, but the person whose status is being changed.

## Cross-cutting concerns

- **Auth**: Requires skipper-level permissions or ownership of the event to execute the associated route.
- **Side effects**: Updates the crew roster status, which may affect the visibility of the person in the event's participant list.

## External consumers

- None known.
