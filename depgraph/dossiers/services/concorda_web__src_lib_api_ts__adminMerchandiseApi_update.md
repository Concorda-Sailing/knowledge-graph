---
node_id: concorda-web::src/lib/api.ts::adminMerchandiseApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 934e7f5eeaf2468869e02340419591935e5647816a2f26ee3ba29b915aa6765a
status: current
---

# adminMerchandiseApi.update

## Purpose

Provides a method to update an existing merchandise item via a `PUT` request. It is part of the `adminMerchandiseApi` service, which handles administrative CRUD operations for the platform's merchandise catalog. Use this when a user is editing an existing product's details in the admin dashboard.

## Invariants

- **Method is `PUT`** — strictly follows the RESTful pattern for updates.
- **Requires `id` and `data`** — the first argument is the item identifier, and the second is the `MerchandiseUpdate` object.
- **Returns a single `Merchandise` object** — the response contains the updated state of the item.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to authorize the request.

## Gotchas

- **Requires `MerchandiseUpdate` shape** — the `data` object must match the interface to ensure all fields are correctly stringified for the `body`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has administrative privileges.
- **Side effects**: Updates to merchandise via this method will affect the visibility and availability of items on the public-facing shop/storefront.

## External consumers

- `MerchandisePage` in `src/app/members/admin/products/merchandise/page.tsx`.
