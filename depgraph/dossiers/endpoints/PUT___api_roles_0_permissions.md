---
node_id: PUT::/api/roles/{0}/permissions
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c1b4287c0c7299f72c5c43e140003c62a67cfa7ab460014e857c456fa702d425
status: current
---

# PUT /api/roles/{role_name}/permissions

## Purpose

Updates the set of permissions associated with a specific role. This endpoint is used to replace the existing permission list with a new one provided in the request body. It is distinct from role creation or user-role assignment, as it focuses strictly on the permission-to-role mapping.

## Invariants

- **Requires `admin.roles.edit` permission** via the `require_permission` dependency.
- **Input is `UpdateRolePermissionsRequest`**, which contains a list of permission names.
- **The operation is a full replacement** of the role's current permissions with the provided list.
- **Returns `RoleWithPermissionsResponse`** containing the updated role object.
- **Throws 404** if the `role_name` provided in the path does not exist.
- **Throws 400** if any permission name in the request body does not exist in the database.

## Gotchas

- **Prevents privilege escalation** via a strict level check. An actor cannot edit a role that has a higher `role.level` than their own maximum role level. This is a critical security guard to prevent lower-level admins from granting themselves elevated permissions.
- **Recent security hardening** (commit `33a37a3`) specifically addressed PII and privilege gaps in the roles and directory modules; any changes to this endpoint must be audited against the "close PII / privilege gaps" requirement.
- **Strict ordering of `role.level` check**: The check `if role.level > actor_max` ensures that even if a user has `admin.roles.edit` permissions, they are still restricted by the hierarchy of the role they are attempting to modify.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.edit` permission.
- **Audit**: N/A.
- **Rate limit**: None specified.
- **Side effects**: Changes to role permissions will immediately affect the authorization logic for any user currently assigned to that role.

## External consumers

- `concorda-web::src/lib/api.ts::rolesApi.updatePermissions`
