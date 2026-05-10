---
node_id: PUT::/api/events/{0}/sailing-event/crew-assign
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0b47d045c703930f432ca71fb9dd4af1e5ec3493c7c19f4f6a8ddf286ee9b97d
status: current
---

# PUT /api/events/{event_id}/sailing-event/crew-assign

## Purpose

Allows an event owner to assign a crew member to a specific position. If the person is not already part of the event's crew, the method automatically creates a new `EventCrew` record with a `status="pool"` to facilitate the transition from a general pool to a specific role. Use this instead of manual database manipulation when moving users into roles for a specific sailing event.

## Invariants

- **Method/Path**: `PUT /{event_id}/sailing-event/crew-assign`.
- **Auth**: Requires `require_auth` and the user must be the `owner` of the sailing event (verified via `_get_user_sailing_event_or_404`).
- **Return Shape**: Returns an `EventCrewRead` object.
- **Automatic Creation**: If the `person_uuid` does not exist in the current event's crew, a new record is initialized with `status="pool"` and `self_selected=False`.

## Gotchas

- **Status Transition**: The method explicitly sets `self_selected = False`. This ensures that even if a user originally joined the event via a self-selection flow, being assigned to a specific position by an owner overrides that intent.
- **Implicit Pool Entry**: Because this method can create a new `EventCrew` record on the fly, callers should be aware that this is a side-effect-heavy operation that can expand the event's crew list.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates ownership via `_get_user_sailing_event_or_404`.
- **Websocket**: Emits `EVENT_CREW_UPDATED` via `broadcast_event` upon successful commit.
- **Side effects**: Triggers updates to the event's crew list, which may affect UI components listening for `EVENT_CREW_UPDATED`.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.assignEventCrew`
