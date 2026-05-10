---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 72612730030e4847f6c33b526d24d65e2e018f13aceaffa9634b88bb40bc8bca
status: current
---

# adminProductsApi.update

## Purpose

Provides the interface for updating existing product records via the `/api/products/{id}` endpoint. It is part of the `adminProductsApi` service, used specifically for administrative modifications to products (Memberships or Events). Use this method when an administrator needs to modify properties of a `TemporalProduct` that are not covered by the initial creation payload.

## Invariants

- **HTTP Method is `PUT`** — unlike the `create` method which uses `POST`, this method performs a full replacement/update of the resource.
- **Requires a valid `id`** — the first argument must be the unique identifier for the product being modified.
- **Returns `Product`** — the response shape is the full `Product` object, not the `ProductUpdate` input shape.
- **Uses `fetchApiAuthenticated`** — requires a valid session/bearer token to execute.

## Gotchas

- **Schema mismatch on update** — per `bf15808`, the API is sensitive to shape-matching; ensure the `ProductUpdate` object aligns with the expected backend structure to avoid rejection.
- **Dependency on `fetchApiAuthenticated`** — if the authentication layer fails or the token is expired, this method will fail with a 401/403 before reaching the product logic.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Updates to products (specifically those with `category: "Event"`) may impact the visibility of event-related data in the schedule or detail views.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailContent` (via `adminProductsApi.update`)
