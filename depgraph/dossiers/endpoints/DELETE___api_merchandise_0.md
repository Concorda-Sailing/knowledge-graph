---
node_id: DELETE::/api/merchandise/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 558e0fe6919252dd5893f8fa9f8065dc2b8c70da4b31d87fc9ef3b64d93063b5
status: llm_drafted
---

# DELETE /api/merchandise/{item_id}

## Purpose

The endpoint for permanently removing a merchandise item from the database. It is used by administrative interfaces to clean up inventory or remove misconfigured items. Unlike the `PUT` method in this module which updates item attributes, this method performs a hard delete of the record.

## Invariants

- **HTTP Method is `DELETE`** — returns `204 No Content` on success.
- **Requires `admin.memberships.manage` permission** — enforced via the `require_permission` dependency.
- **Input is `item_id` (string)** — the unique identifier for the `Merchandise` model instance.
- **Returns 404 if the item does not exist** — the check occurs before the deletion attempt.

## Gotchas

- **Hard deletion** — this method performs a `db.delete(item)` followed by a `db.commit()`. There is no soft-delete or "archived" state implemented here; once called, the record is gone from the database.

## Cross-cutting concerns

- **Auth**: Requires `require_permission("admin.memberships.manage")`.
- **Audit**: N/A.
- **Side effects**: Deleting an item will remove it from the visibility of any frontend component or user-facing list that queries the `Merchandise` table.

## External consumers

- `concorda-web::src/lib/api.ts::adminMerchandiseApi.delete`
