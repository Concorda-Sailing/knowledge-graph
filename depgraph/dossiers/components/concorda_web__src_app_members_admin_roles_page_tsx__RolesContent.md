---
node_id: concorda-web::src/app/members/admin/roles/page.tsx::RolesContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 791b3d16aafc064e24353ca5417c8e21e2b2f432d91ec4c04a33bb6313bdd5d5
status: current
---

# RolesContent

## Purpose

The `RolesContent` component renders the administrative interface for viewing and selecting organization roles. It performs an initial fetch of all available roles via `rolesApi.list()` and then performs a secondary fetch for each role's specific permission set via `rolesApi.get(role.name)` to ensure the UI has the full permission payload. This component is the core of the roles management view, providing the list of cards that users click to initiate editing.

## Invariants

- **Permission Gate Requirement**: The component must be wrapped in a `<PermissionGate permission="admin.roles.assign">` (provided by the parent `RolesPage`) to prevent unauthorized access to the API calls.
- **Two-step Fetch Pattern**: The component relies on a sequential fetch pattern: first fetching the list of role names, then fetching the full `RoleWithPermissions` object for each name.
- **Key Identity**: The `role.name` is used as the unique identifier for both the `key` in the list mapping and the selection state.
- **Error State UI**: If the `rolesApi` calls fail, the component must render an `<Alert>` with the error message to inform the admin of the failure.

## Gotchas

- **Sequential API dependency**: The `loadRoles` function uses `Promise.all` on a map of `rolesApi.get(r.name)`. If the number of roles grows significantly, this could trigger rate limits or high latency due to the N+1 request pattern.
- **Role Selection State**: `selectedRole` is updated via `setSelectedRole(role.name)` on click, but the current implementation of `RolesContent` does not yet provide a way to edit the role or view its details beyond the card click; it only sets the state.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.assign` permission via the `PermissionGate` in the parent component.
- **Audit**: Changes to roles (though not implemented in this specific view) are typically audited via the `rolesApi`.
- **Side effects**: Re-rendering this component or its parent is necessary to refresh the list if roles are modified via a different administrative interface.

## External consumers

None known.
