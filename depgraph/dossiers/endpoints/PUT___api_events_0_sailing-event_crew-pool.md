---
node_id: PUT::/api/events/{0}/sailing-event/crew-pool
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 629064e8438bdb7eb57b5f7f43f98c9250d7cbe05896735f79a85eea441a7053
status: llm_drafted
---

# PUT /api/events/{event_id}/sailing-event/crew-pool

## Purpose

Synchronizes the "crew pool" for a specific sailing event. It allows an owner to either provide a simple list of person UUIDs (where position in the list determines priority) or a rich list of members with explicit roles and priorities. This is the primary mechanism for managing the group of people associated with an event before or during a race.

## Invariants

- **Method/Path**: `PUT /{event_id}/sailing-event/crew-pool`.
- **Auth**: Requires `require_auth` and the user must be the `owner` of the sailing event (verified via `_get_user_sailing_event_or_404`).
- **Return Shape**: Returns a `list[EventCrewRead]`.
- **Deletion Logic**: Only members with `status == "pool"` are removed from the database if they are missing from the incoming request.

## Gotchas

- **Status-dependent deletion**: Per `dd72f2f`, the logic only deletes existing `EventCrew` rows if their status is exactly `"pool"`. If a user is in a different status (e.g., a permanent crew member), they are not removed by this sync, which could lead to unexpected persistence of members.
- **Implicit Role/Priority**: In "Simple" mode (when `data.members` is null), the API automatically assigns the `"main"` role and uses the list index as the `priority`.

## Cross-cutting concerns

- **Auth**: Requires `owner` relation via `_get_user_sailing_event_or_404`.
- **Websocket**: Emits `EVENT_CREW_UPDATED` for the given `event_id` upon successful commit.
- **Side effects**: Updates the crew list used by the schedule detail page and any components relying on the `EventCrew` status/role.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.setCrewPool` (Web frontend)
- `concorda-test::lib/api-client.ts::ApiClient.setEventCrewPool` (Test suite)
