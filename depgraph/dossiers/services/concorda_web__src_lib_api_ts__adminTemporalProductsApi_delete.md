---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2c525deb6c23123198dbbc18eb4003588d4d6f932d5cb86169d704f32701af77
status: llm_drafted
---

# adminTemporalProductsApi.delete

## Purpose

The `delete` method for `adminTemporalProductsApi` performs a destructive operation on a specific temporal product resource. It is used by administrators to remove a product from the system via a `DELETE` request to the `/api/temporal-products/{id}` endpoint.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to target the specific resource ID.
- **Returns `void`** — The function returns a promise that resolves to nothing upon successful deletion.
- **Requires `fetchApiAuthenticated`** — The operation is protected by the standard authentication guard.

## Gotchas

- **Destructive side effect** — While no specific regression is noted in recent history for this specific method, it is part of the `adminTemporalProductsApi` suite which manages critical product lifecycle data.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has administrative privileges.
- **Side effects**: Deleting a product may affect the visibility of temporal products in the admin dashboard and any dependent product-listing views.

## External consumers

- `concorda-web::src/app/members/admin/products/[category]/page.tsx` (via `CategoryProductsPage`)
