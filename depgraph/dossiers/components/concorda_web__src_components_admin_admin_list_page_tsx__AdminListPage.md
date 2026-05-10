---
node_id: concorda-web::src/components/admin/admin-list-page.tsx::AdminListPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bba44fd171d05f840e9d4703194f1a6df88bc573e653ec969d002d204422234e
status: llm_drafted
---

# AdminListPage

## Purpose

The primary view for the administrative user management interface. It acts as a wrapper around `AdminListPageInner` to optionally enforce a `PermissionGate` based on the provided `permission` prop. Use this component when building administrative views that require a specific permission level to be verified before the underlying list logic is even initialized.

## Invariants

- **Optional Permission Guard**: If the `permission` prop is provided, the component must wrap the inner content in a `<PermissionGate>`.
- **Prop Passthrough**: The `...props` are passed directly to `AdminListPageInner`, ensuring that any state or configuration managed by the parent is preserved.
- **Render Logic**: If `permission` is undefined, the component renders `AdminListPageInner` directly without any authorization wrapping.

## Gotchas

- **Permission bypass risk**: Because the `permission` prop is optional, failing to pass a permission string when building a new admin route will bypass the `PermissionGate` entirely, potentially exposing sensitive user data to non-admin users.

## Cross-cutting concerns

- **Auth**: Uses `PermissionGate` to control access to the administrative user list.
- **Side effects**: Changes to user status or administrative data within this page (via `DeleteConfirmDialog`) will affect the visibility of users in the global admin dashboard.

## External consumers

None known.
