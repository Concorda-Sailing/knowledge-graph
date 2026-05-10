---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 69ab9f829c8fdce2abdaf8ec58281ee71fc51fb40646182a780564514c51302b
status: current
---

# adminTemporalProductsApi.create

## Purpose

The `create` method handles the creation of new `TemporalProduct` entries via the admin API. It is part of the `adminTemporalProductsApi` service, which manages the lifecycle of time-bound products (likely seasonal merchandise or event-specific items). Use this method when an administrator needs to instantiate a new product with a specific set of attributes defined by `TemporalProductCreate`.

## Invariants

- **Method is POST** — Sends a request to the `/api/temporal-products` endpoint.
- **Requires `fetchApiAuthenticated`** — The request must include a valid bearer token; it will fail if the user is not authenticated.
- **Input is `TemporalProductCreate`** — The body must strictly follow the shape of the `TemporalProductCreate` interface to avoid 400 errors.
- **Returns `TemporalProduct`** — On success, the API returns the fully constructed object, including server-generated fields like `id`.

## Gotchas

- **Admin-only access** — While the code itself doesn't show a permission check, the `fetchApiAuthenticated` wrapper and the `admin` prefix in the service name imply this is restricted to administrative roles.
- **Ordering dependency** — The existence of the `reorder` method in the same service suggests that product sequence is a managed property; creating a product may require a subsequent call to `reorder` to maintain a specific display sequence.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to attach credentials.
- **Side effects**: Successful creation/updates to temporal products may impact the visibility of items in admin-facing dashboards or category-specific product lists.

## External consumers

- `concorda-web::src/app/members/admin/products/[category]/page.tsx` (via `CategoryProductsPage`)
