---
node_id: concorda-web::src/lib/api.ts::adminEventDiscountsApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aae07e3ed9fcea5fbd68cea968cacf86dbe458da961331a2d5800f0e01c529d4
status: current
---

# adminEventDiscountsApi.delete

## Purpose

The `delete` method for `adminEventDiscountsApi` removes a specific discount associated with an event. It is used by administrators to manage event-specific pricing or promotional structures. Use this when a discount is no longer valid or was created in error, rather than using `update` to modify an existing discount's properties.

## Invariants

- **HTTP Method is `DELETE`** — strictly follows RESTful patterns for resource removal.
- **Requires `eventId` and `id`** — both the parent event identifier and the specific discount identifier are required to construct the URI.
- **Returns `void`** — the function returns a promise that resolves to nothing upon successful deletion.
- **Uses `fetchApiAuthenticated`** — requires a valid session/token to authorize the request.

## Gotchas

- **Dependency on `eventId` context** — the endpoint is nested under `/api/events/${eventId}/discounts/${id}`. If the `eventId` provided does not match the owner of the discount, the request will fail (likely with a 404 or 403).
- **UI State Sync** — since this is a destructive action, any UI components displaying the event's discount list (like the `EventDetailContent` in `page.tsx:817`) must be refreshed or re-fetched to reflect the removal.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`, requiring an active admin-level session.
- **Side effects**: Deleting a discount will immediately change the price/total calculation for any users viewing the event detail or checkout flow.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (via `EventDetailContent`)
