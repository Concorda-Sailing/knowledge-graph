---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87fb731ec6efa911db21e9bfc19da83e261948ec78cbcca400b72d2b19f255a0
status: llm_drafted
---

# adminProductsApi.create

## Purpose
`adminProductsApi.create` is a service method used to persist new product entities (Memberships or Events) to the backend. It is distinct from the `list` or `get` methods by performing a state-changing `POST` operation. A future agent should reach for this when implementing administrative interfaces that require creating new revenue or service-based products, ensuring the payload matches the `ProductCreate` interface.

## Invariants
* Uses `POST` method on the `/api/products` endpoint.
* Requires authenticated access via `fetchApiAuthenticated`.
* Returns a `Promise<Product>` representing the newly created resource.
* The payload must conform to the `ProductCreate` type (defined near line 2536).

## Gotchas
* Ensure the `slug` provided in the `ProductCreate` payload is unique and URL-friendly to avoid backend validation failures.
* The `category` must be one of the valid `ProductCategory` values ("Membership" or "Event") to satisfy the type system and server-side logic.

## Cross-cutting concerns
* **Auth**: Requires a valid session/token via `fetchApi-authenticated` wrapper.
* **Side Effects**: Creating a product may impact event-related logic or membership availability in the dashboard.

## External consumers
* `concorda-web::src/app/members/admin/events/[id]/page.tsx` (via `EventDetailContent`)

## Open questions
* None.
