---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.reorder
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e9567054eee377a4d98c9f1681e3ca674fd314de2745e5519bf20063ca28cd6f
status: llm_drafted
---

# adminTemporalProductsApi.reorder

## Purpose

Updates the display order of temporal products by accepting an array of IDs. This is used to persist custom sorting logic (e.g., drag-and-drop reordering in the admin UI) to the backend. It is distinct from `update`, which modifies individual product properties; `reorder` specifically handles the sequence of the collection.

## Invariants

- **Method is `PUT`** — The request must use the PUT method to the `/api/temporal-products/reorder` endpoint.
- **Input is an array of strings** — The body must be a JSON object with the key `ids` containing an array of product identifiers.
- **Returns a success message** — The expected response shape is `{ message: string }`.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the request is authorized.

## Gotchas

- **Ordering is absolute** — The order of the `ids` array determines the new sequence in the database. If an ID is omitted from the array, it may be moved to the end of the list or handled according to backend logic (verify if the backend supports partial reordering).

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Reordering affects the display sequence of products in the `CategoryProductsPage`.

## External consumers

- `CategoryProductsPage` in `src/app/members/admin/products/[category]/page.tsx`.
