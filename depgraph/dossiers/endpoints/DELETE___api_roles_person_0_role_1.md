---
node_id: DELETE::/api/roles/person/{0}/role/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c604a0c5018f88ff0110261a146d9f76005cb4f1f2fd9e3323c8949b442a276d
status: llm_drafted
---

# DELETE /api/roles/person/{person_id}/role/{role_name}

## Purpose

Removes a specific role assignment from a user. This endpoint is used by administrators to downgrade or strip permissions. It is distinct from the `PUT` update endpoint; while `PUT` modifies existing roles, this `DELETE` method removes the `UserRole` record entirely from the database.

## Invariants

- **Requires `admin.roles.edit` permission** via the `require_permission` dependency.
- **Prevents privilege escalation** — the `current_user` cannot revoke a role that has a higher `level` than their own highest assigned role.
- **Input `role_name` is a string identifier** used to look up the `Role` object before attempting deletion.
- **Returns a 404** if the `role_name` does not exist or if the specific `person_id`/`role_id` combination is not found in the `UserRole` table.

## Gotchas

- **Privilege gap protection** — per commit `33a37a3`, this method enforces a strict hierarchy check. An admin can only revoke roles that are at or below their own maximum role level. If an admin attempts to revoke a role with a higher `level` than their own, the request fails with a 403.
- **`organization_id` is optional but critical** — if provided, the `user_role` lookup is scoped to that specific organization. If the user has the role globally but not within the provided `organization_id`, the endpoint returns a 404.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.edit` permission.
- **Audit**: N/A.
- **Side effects**: Changes to user roles via this endpoint will affect the visibility of users in the directory and their access levels in the dashboard.

## External consumers

None known.
