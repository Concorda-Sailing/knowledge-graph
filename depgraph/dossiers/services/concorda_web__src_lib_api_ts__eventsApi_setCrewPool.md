---
node_id: concorda-web::src/lib/api.ts::eventsApi.setCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6458ea33385e81cfe01d4def9e2b7b06c47c40c432dee485c09fd137e50b0eb6
status: current
---

# eventsApi.setCrewPool

## Purpose

The `setCrewPool` method is responsible for overwriting the current list of members associated with a specific sailing event. It provides a way to either pass a list of specific `personUuids` or a more complex `members` object (containing `CrewPoolMember` data). This is distinct from `assignEventCrew`, which targets a single person and position, as `setCrewPool` is intended for bulk updates or full-state synchronization of the event's crew roster.

## Invariants

- **HTTP Method is `PUT`** — This is a replacement operation, not an additive one.
- **Endpoint is `/api/events/${eventId}/sailing-event/crew-pool`**.
- **Body is polymorphic** — It accepts either `{ person_uuids: string[] }` or `{ members: CrewPoolMember[] }`.
- **Returns `EventCrewMember[]`** — The response provides the updated list of members for the event.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the caller has permission to modify event state.

## Gotchas

- **Bulk replacement vs. Incremental update** — Because this uses `PUT`, calling this with a partial list will wipe out existing members not included in the payload.
- **Payload shape sensitivity** — The method uses a ternary to decide whether to send `members` or `person_uuids`. If the API contract changes to require one specific key, this logic will break.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Updates the state of the event, which may affect the visibility of the crew list in the event detail view.

## External consumers

- `EventCrewPoolSelector` in `concorda-web::src/components/dashboard/event-crew-pool-selector.tsx`.
