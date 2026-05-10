---
node_id: concorda-web::src/lib/api.ts::eventsApi.removeEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9b6e94a47e817825c3641b5a9bed4ec38a72e7e8ab601b28d778ec86d05354a4
status: current
---

# eventsApi.removeEventCrew

## Purpose

Removes a specific person from an event's crew list. This is used to manage crew composition by deleting the association between an event and a person. It is distinct from `markCrewResponse`, which only changes the status of a request, whereas this method completely severs the relationship.

## Invariants

- **HTTP Method is `DELETE`** — The endpoint expects a deletion request to the specific resource path.
- **Path structure is `/api/events/${eventId}/sailing-event/crew/${personUuid}`** — Both the event ID and the person's UUID are required to target the correct resource.
- **Returns `void`** — A successful call returns an empty body.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute.

## Gotchas

- **Recent decoupling of schedule/detail logic** — Per commit `1b5d864`, the API structure was adjusted to ensure the detail page doesn't rely on coupled state; ensure any UI calling this doesn't assume the person is still "attached" to the event in the local cache immediately after the call.
- **Dependency on `personUuid`** — The method requires the specific UUID of the person being removed, not just a name or a role.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Deleting a crew member may affect the display of the "accepting-crew" status or the count of active crew members on the regatta detail page.

## External consumers

- `EventCrewCard` in `src/components/dashboard/event-crew-card.tsx` (via hook calls at `event-crew-card.tsx:122` and `145`).
