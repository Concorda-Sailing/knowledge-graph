---
node_id: GET::/api/profile/event-registrations
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3928fc5be61cfc1f5ca8869599f9fdab2d08e00396f7995dd57e2d4c6126c9ad
status: llm_drafted
---

# GET /api/profile/event-registrations

## Purpose

Retrieves a list of all event registrations associated with the currently authenticated user. It performs a join across `EventRegistration`, `Event`, and `Product` to provide a flattened view of registration details, including the event's name, date, location, and the specific ticket/product price. This is the primary endpoint for the "My Registrations" view in the user profile.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a list of `MyEventRegistration` objects**, containing both event metadata and ticket/product details.
- **Orders by `Event.date` descending**, ensuring the most upcoming or recent events appear first.
- **Filters strictly by `current_user.id`**, preventing users from seeing registrations belonging to others.

## Gotchas

- **Security/IDOR protection**: Per commit `c9a7c41` (`security: tier-A IDOR audit fixes`), ensure that any logic added to this or related profile endpoints maintains strict ownership checks to prevent unauthorized data exposure.
- **Data integrity**: The endpoint relies on a three-way join between `EventRegistration`, `Event`, and `Product`. If an event or product is deleted without a cascade, this query may fail or return incomplete results depending on the DB state.

## Cross-cutting concerns

- **Auth**: Requires a valid session via `require_auth`.
- **Audit**: N/A.
- **Side effects**: N/A.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.getEventRegistrations` (used for the user's personal registration dashboard).

## Open questions

- Should the response include a `status` filter (e.g., only showing "Confirmed" vs "Cancelled") to allow the UI to filter out cancelled registrations via query parameters?
