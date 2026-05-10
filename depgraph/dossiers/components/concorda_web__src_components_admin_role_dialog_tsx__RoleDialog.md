---
node_id: concorda-web::src/components/admin/role-dialog.tsx::RoleDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5fa7585e23ca95f77b0758338e683fcbbd30cdd6de7ef1570509f36ac7593511
status: current
---

# RoleDialog

## Purpose

The `RoleDialog` provides a UI for administrators to view and modify the specific permissions associated with a given role. It fetches both the current role data and the full list of available permissions to present a categorized view of what can be toggled. Use this component when an admin needs to perform granular permission editing for a specific role rather than a global role management view.

## Invariants

- **Requires `roleName` and `open` state** — The component remains idle and does not fetch data until `open` is true and a valid `roleName` is provided.
- **Fetches two distinct resources** — It performs a concurrent fetch of the specific role via `rolesApi.get(roleName)` and the global permission list via `rolesApi.listPermissions()`.
- **State-driven selection** — The `selectedPermissions` state is a `Set<string>` derived from the `roleData.permissions` array to ensure efficient lookups during toggling.
- **Returns void on success** — The `onSuccess` callback is triggered only after a successful `rolesApi.updatePermissions` call, and the dialog is closed via `onOpenChange(false)`.

## Gotchas

- **Mobile layout constraints** — Per commit `0564f06`, the dialog uses `sm:max-w-[550px]` and `max-h-[90vh]` with `overflow-y-auto` to ensure the permission list remains scrollable and doesn't break the viewport on smaller screens.
- **Category formatting** — The `formatCategory` helper expects a dot-notated string (e.g., `"admin.user.edit"`) to transform it into a human-readable breadcrumb (`"Admin > User > Edit"`).

## Cross-cutting concerns

- **Auth**: Requires an authenticated session with administrative privileges to successfully call `rolesApi.updatePermissions`.
- **Side effects**: Successful updates trigger the `onSuccess` callback, which is typically used by parent admin pages to trigger a re-fetch of the roles list.

## External consumers

None known.
