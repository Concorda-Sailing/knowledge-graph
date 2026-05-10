---
node_id: concorda-web::src/lib/api.ts::adminEventDiscountsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6aa2fd294d679cd559ec1ae01b8be4ec53aae27b1c0efc6ad29c6e91baa26a20
status: current
---

# adminEventDiscountsApi.update

## Purpose

Provides the interface for updating existing event-specific discounts. It is part of the `adminEventDiscountsApi` group, which handles the lifecycle of discount objects (create, list, update, delete) for a specific event. Use this method when an administrator needs to modify the properties of an existing discount, such as its name or value, via a `PUT` request.

## Invariants

- **HTTP Method is `PUT`** — This is a full replacement of the `EventDiscount` resource.
- **Requires `eventId` and `id`** — The path is structured as `/api/events/${eventId}/discounts/${id}`.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token; this is an administrative action.
- **Returns `Promise<EventDiscount>`** — On success, the API returns the updated discount object.

## Gotchas

- **Path dependency** — The method relies on both the `eventId` and the specific discount `id`. If the `eventId` provided does not match the owner of the discount, the request will fail (likely a 404 or 403).
- **Admin-only access** — Because it uses `fetchApiAuthenticated`, this method is strictly for authenticated sessions.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Updates to this endpoint will change the discount data visible on the `EventDetailContent` page in the admin dashboard.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (via `EventDetailContent`)
