---
node_id: POST::/api/merchandise
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eb27e4ea03951aa52f8498243220b7ed1ad89db1e39cd9f62e4153bd8db3dc57
status: llm_drafted
---

# POST /api/merchandise

## Purpose

Creates a new merchandise item in the database. This endpoint is used by the admin dashboard to populate the shop inventory. It is distinct from the `PUT` endpoint in that it enforces strict uniqueness constraints on both `slug` and `stock_number` for new entries to prevent duplicate product identifiers.

## Invariants

- **HTTP Method is POST** and returns `status_code=201`.
- **Requires `admin.memberships.manage` permission** via the `_user` dependency.
- **Input must be a `MerchandiseCreate` object** containing a valid `slug`.
- **Returns a `MerchandiseRead` object** upon successful creation.
- **Uniqueness is enforced** on both `slug` and `stock_number` at the time of creation.

## Gotchas

- **Slug and Stock Number collisions:** The endpoint raises a 400 error if the provided `slug` or `stock_number` already exists in the database. This is a hard constraint to prevent broken product links or inventory confusion.
- **Dependency on `require_permission`:** If the user lacks the `admin.memberships.manage` permission, the request will fail before reaching the logic, as seen in the `_user` dependency.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage` permission.
- **Side effects**: Creation of a new item may affect the visibility of merchandise in the public-facing shop components.

## External consumers

- `concorda-web::src/lib/api.ts::adminMerchandiseApi.create`
