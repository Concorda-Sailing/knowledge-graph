---
node_id: concorda-web::src/components/admin/role-dialog.tsx::formatCategory
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1bb00e5063b5b533764cbead7eeeabb52f72b75d00bfb15d01c5cd2d17a48935
status: current
---

# formatCategory

## Purpose

The `formatCategory` helper transforms dot-notated permission strings into a human-readable breadcrumb format. It splits a string by the `.` delimiter, capitalizes the first letter of each segment, and joins them with a ` > ` separator (e.g., `"user.edit"` becomes `"User > Edit"`). This is used within the `RoleDialog` to visually group and display permissions in the admin interface.

## Invariants

- **Input is a dot-delimited string.** The function expects a string like `category.subcategory`.
- **Output is a display-only string.** It is used for UI rendering and does not represent the actual permission key used for logic or API calls.
- **Case transformation is shallow.** It only capitalizes the first character of each segment; it does not handle complex casing or mid-word capitalization.

## Gotchas

- **Width constraints on mobile.** Per commit `0564f06`, admin dialogs (including this one) require careful handling of width and stacking to ensure the formatted category strings do not break the layout on smaller screens.

## Cross-cutting concerns

- **Auth**: None. (This is a pure string utility used within an authenticated admin component).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: None.

## External consumers

None known.
