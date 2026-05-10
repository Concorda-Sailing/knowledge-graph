---
node_id: POST::/api/roles/assign
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7781de131e8dd08dd92f5cf9b061d51df4b5b64ec896f6e118229463d3623479
status: llm_drafted
---

# POST /api/roles/assign

## Purpose

Assigns a specific role to a user within a given organization. It is the primary mechanism for elevating user privileges or granting access to specific organizational resources. This endpoint is distinct from the `revoke_role` endpoint, which handles the removal of assignments.

## Invariants

- **Requires `admin.roles.edit` permission** via the `require_permission` dependency.
- **Enforces privilege hierarchy**: The `assigner_max_level` must be greater than or equal to the `role.level` being assigned.
- **Returns `UserRoleResponse`**: Includes the `id`, `person_id`, `role_id`, `role_name`, `role_display_name`, `organization_id`, and `assigned_at` timestamp.
- **Throws 404** if either the `person_id` or the `role_name` does not exist in the database.
- **Throws 400** if the user already possesses the role within the specified `organization_id`.

## Gotchas

- **Privilege escalation protection**: Per commit `33a37a3`, this endpoint implements a strict check to ensure an admin cannot assign a role with a higher level than their own. This was added to close a PII/privilege gap in the roles system.
- **Role level dependency**: The logic relies on `role.level` (an integer). If a role is created or updated with a level higher than existing admins, those admins will be unable to assign it, potentially locking out certain administrative flows.

## Cross-cutting concerns

- **Auth**: Requires `AuthUser` with `admin.roles.edit` permission.
- **Audit**: Writes to the `UserRole` table, capturing the `assigned_by` field (the `current_user.id`).
- **Side effects**: Changes to roles via this endpoint will affect user access levels across the platform, including visibility in the directory and access to organization-specific features.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.assignRole` (Playwright test suite).
