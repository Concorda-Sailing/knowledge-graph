---
node_id: concorda-web::src/lib/api.ts::rolesApi.updatePermissions
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a7320758172bb9b1f9f227fb82cf86fccc937349864fad2c9a6722861f40aa0f
status: llm_drafted
---

# rolesApi.updatePermissions

## Purpose

Updates the set of permissions associated with a specific role. It is used by administrative interfaces to modify what actions a role (e.g., "Admin", "Crew") is authorized to perform. Use this instead of `rolesApi.get` when you need to perform a full overwrite of the permission set for a given role name.

## Invariants

- **Method is `PUT`** — This is a destructive update of the permission list, not a patch.
- **Requires `name` and `permissions`** — The first argument is the role name (string), and the second is an array of permission strings.
- **Returns `RoleWithPermissions`** — A successful call returns the updated role object, including its new permission set.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token; calls will fail if the user is not authenticated or lacks sufficient privileges.

## Gotchas

- **Destructive overwrite** — Because this uses `method: "PUT"`, the `permissions` array passed in becomes the absolute source of truth for that role. If you omit a permission that was previously present, it will be removed from the role.
- **Role name dependency** — The endpoint is constructed via template literal `` `/api/roles/${name}/permissions` ``. If the `name` contains special characters or doesn't match the expected API routing pattern, the request will fail.

## Cross-cutting concerns

- **Auth**: Depends on `fetchApiAuthenticated`; requires an active session with administrative privileges.
- **Side effects**: Updates to permissions via this method will immediately affect the authorization logic for any user assigned to the modified role.

## External consumers

- `RoleDialog` in `concorda-web/src/components/admin/role-dialog.tsx` (via `role-dialog.tsx:95`).
