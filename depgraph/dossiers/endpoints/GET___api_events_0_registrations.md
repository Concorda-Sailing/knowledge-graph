---
node_id: GET::/api/events/{0}/registrations
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9d07baeed58d9c87a91954e7049255d66eb5fdb5f3e7013e634ed67d5a161e55
status: current
---

# GET /api/events/{event_id}/registrations

## Purpose

Retrieves a list of all registrations associated with a specific event. This is an administrative endpoint used to audit who is signed up for an event, ordered by creation date descending. It is distinct from user-facing endpoints that might filter visibility based on roles; this returns the full list of `EventRegistration` objects for the given `event_id`.

## Invariants

- **HTTP Method**: `GET`.
- **Path**: `/api/events/{event_id}/registrations`.
- **Auth Requirement**: Requires `events.edit` permission via `require_permission("events.edit")`.
- **Return Shape**: A list of `EventRegistrationRead` objects.
- **Ordering**: Results are strictly ordered by `EventRegistration.created` in descending order.
- **Error State**: Returns a `404 Not Found` if the `event_id` does not exist in the database.

## Gotchas

- **Permission Rigidity**: Because it depends on `require_permission("events.edit")`, this endpoint will fail for users with read-only roles. If a "viewer" role needs to see registrations, this endpoint is the wrong choice.
- **Data Integrity**: The `event_id` must be a valid UUID string; the router expects a string that matches the `Event` primary key.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission.
- **Side effects**: Data returned here is used by administrative views to manage event participation.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.getRegistrations` (via `api.ts:613`)
