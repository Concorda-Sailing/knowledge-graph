---
node_id: concorda-web::src/components/admin/role-dialog.tsx::groupByCategory
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1dbea3aea2a37ac6f0882a7aab988f9deb7936b550cafe201b50e18c921d96c1
status: llm_drafted
---

# groupByCategory

## Purpose

A utility function that partitions an array of `Permission` objects into a record keyed by their category. It is used to organize the permission list for display within the `RoleDialog` UI, allowing the admin to see permissions grouped by functional area (e.g., "User Management" vs "Billing").

## Invariants

- **Input is an array of `Permission` objects.** Each object must contain a `category` string property.
- **Output is a `Record<string, Permission[]>`**. The keys are the exact strings found in `perm.category`.
- **Preserves all permissions.** Every permission passed in the input array is present in exactly one group in the output.

## Gotchas

- **Category string format affects UI hierarchy.** While this function only groups, the `formatCategory` function in the same file is responsible for the visual "breadcrumb" style (e.g., `part.toUpperCase()`). If a category name contains dots, it is split and transformed into a " > " separator.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges to use the resulting data, as the `RoleDialog` relies on `rolesApi` which is restricted to admin roles.
- **Side effects**: Changes to the groupings in this component indirectly affect the `rolesApi.updatePermissions` call when a user saves the dialog.

## External consumers

None known.
