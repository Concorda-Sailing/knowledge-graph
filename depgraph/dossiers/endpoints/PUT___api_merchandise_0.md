---
node_id: PUT::/api/merchandise/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e17c5665190de43de3494599b9833f4e50f948ccaeb3526074871681e3960313
status: llm_drafted
---

# PUT /api/merchandise/{item_id}

## Purpose

Updates an existing merchandise item's attributes. It is used by the admin dashboard to modify product details like name, slug, or stock number. This method is distinct from the creation endpoint as it performs partial updates via `exclude_unset=True` and enforces uniqueness constraints on the `slug` and `stock_number` relative to the current item.

## Invariants

- **Method is `PUT`** targeting a specific `{item_id}`.
- **Requires `admin.memberships.manage` permission** via the `_user` dependency.
- **Returns `MerchandiseRead` shape** containing the updated object.
- **Uniqueness check is enforced** for both `slug` and `stock_number` if they are provided in the payload.
- **`item.modified` is updated** to `datetime.utcnow()` on every successful update.

## Gotchas

- **Slug and Stock Number collisions**: If an update includes a `slug` or `stock_number` that belongs to a *different* item, the API raises a 400 error. This is explicitly checked in the logic to prevent accidental duplication during edits.
- **Partial updates via `exclude_unset`**: The function uses `data.model_dump(exclude_unset=True)`. If a caller sends a partial payload, only the provided fields are updated; omitted fields remain unchanged in the database.

## Cross-cutting concerns

- **Auth**: Requires `require_permission("admin.memberships.manage")`.
- **Audit**: No explicit audit log entry is generated in this function, though `item.modified` tracks the timestamp.

## External consumers

- `concorda-web`: `adminMerchandiseApi.update` in `src/lib/api.ts`.
