---
node_id: concorda-web::src/components/admin/admin-list-page.tsx::AdminListPageInner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 702fb336e8b5d2e50aab77552886add9eb1f2565a1417518b9fa7ccb11691de2
status: current
---

# AdminListPageInner

## Purpose

The `AdminListPageInner` component provides a standardized layout for administrative views, including a title, subtitle, and action area. It manages the visual state for loading, empty results, and header-driven content (filters/descriptions) to ensure consistency across the admin dashboard. It is the internal implementation of `AdminListPage`, which handles the permission wrapping.

## Invariants

- **`hasCardHeader` logic** — The `CardHeader` and `description` only render if `filters` or `description` are provided.
- **Padding adjustment** — If `hasCardHeader` is false, `CardContent` applies `pt-6` to maintain vertical spacing.
- **Empty state fallback** — If `empty` is true, the component renders the `emptyMessage` (defaulting to "No items found") and an optional `emptyIcon`.
- **Loading priority** — The `loading` prop takes precedence over the `empty` prop; if `loading` is true, the `Loader2` spinner is shown regardless of other states.

## Gotchas

- **Permission wrapping** — The parent `AdminListPage` uses `PermissionGate` to wrap this component. If you are testing or developing this component in isolation, ensure you are interacting with the `AdminListPage` export to verify that the `permission` prop correctly triggers the gate.

## Cross-cutting concerns

- **Auth**: Uses `PermissionGate` in the exported `AdminListPage` to enforce access control.
- **Side effects**: Provides the layout container for admin-level CRUD operations, including the `search-input` and `delete-confirm-dialog` introduced in commit `b6ca664`.

## External consumers

None known.
