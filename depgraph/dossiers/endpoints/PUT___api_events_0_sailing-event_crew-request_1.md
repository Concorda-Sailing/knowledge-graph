---
node_id: PUT::/api/events/{0}/sailing-event/crew-request/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dbc2239d1d1c07e508da06709543047a8d25729a1abddcc808c39056b41baa49
status: llm_drafted
---

# PUT /api/events/{event_id}/sailing-event/crew-request/{person_uuid}

## Purpose

Allows an event owner to accept or decline a pending crew request. When a request is accepted, the user is promoted from a prospective requester to an active member of the boat's crew. This endpoint is distinct from general crew management as it specifically handles the transition from a `requested` status to `accepted` or `declined`.

## Invariants

- **Requires `event_id` and `person_uuid`** in the URL path.
- **Auth requirement**: The `current_user` must be the owner of the sailing event (verified via `_get_user_sailing_event_or_404`).
- **Action validation**: The `data.action` must be exactly `"accept"` or `"decline"`; otherwise, it raises a 400 error.
- **Status transition**: An accepted request promotes the user to `BoatCrew` with `role="crew"` and `status="active"` if they are not already an active member of that boat.
- **Returns `EventCrewRead`**: The response shape is the serialized representation of the updated `EventCrew` record.

## Gotchas

- **Promotion logic is idempotent**: If a user is already an owner or active crew, the endpoint updates their status to `active` and role to `crew` without creating duplicate or conflicting entries (per `_get_user_sailing_event_or_404` logic).
- **Status check requirement**: The endpoint only operates on records where `EventCrew.status == "requested"`. If the status has already been changed, it raises a 404 (per `if not ec` check).
- **Side effect of acceptance**: Accepting a request triggers a broadcast for both the event and the boat (via `broadcast_event("boat_crew.updated", se.boat_uuid)`), which may trigger UI updates in other parts of the app.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and ownership of the event.
- **Websocket**: Emits `EVENT_CREW_UPDATED` for the `event_id` and, if accepted, `boat_crew.updated` for the `boat_uuid`.
- **Side effects**: Updates the `BoatCrew` table to ensure the user is a member of the boat, not just the specific event.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.respondToCrewRequest`
