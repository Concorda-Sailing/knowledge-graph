---
node_id: concorda-web::src/app/members/admin/roles/page.tsx::RolesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f435269defda702d3bfb35519512cea54575cf35c2f7053f01b382ca92a86a49
status: llm_drafted
---

# RolesPage

## Purpose

The `RolesPage` provides the administrative interface for viewing and managing system-wide roles and their associated permissions. It serves as a high-level dashboard that lists available roles and provides a gateway to the `RoleDialog` for editing specific role configurations. It is distinct from individual permission management (which happens at the user level) by focusing on the definition of the roles themselves.

## Invariants

- **Requires `admin.roles.assign` permission** via the `PermissionGate` wrapper to prevent unauthorized access to the role list.
- **Fetches roles via `rolesApi.list()` and `rolesApi.get(name)`** to ensure the full permission set for each role is loaded before rendering.
- **Uses `role.name` as the unique identifier** for both the list key and the selection state.
- **Displays a loading state** using the `Loader2` icon while the asynchronous `loadRoles` function is executing.

## Gotchas

- **Sequential API calls during load:** The component performs a `Promise.all` on `rolesApi.get(r.name)` for every role returned by `list()`. If the number of roles grows significantly, this may lead to high latency or rate-limiting issues on the API side.
- **URL Restructure:** Per commit `fd7fd0f`, this page is part of a recent URL restructure and public page addition; ensure any deep links to admin routes are updated to reflect the new routing structure.

## Cross-cutting concerns

- **Auth**: Guarded by `PermissionGate` with the `admin.roles.assign` permission.
- **Side effects**: Modifying roles via the `RoleDialog` (triggered by clicking a card) will change the permission availability for all users assigned to those roles.

## External consumers

None known.
