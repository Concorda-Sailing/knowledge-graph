---
node_id: GET::/api/roles/person/{0}/permissions
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7ec91b57a79241b68677db09e9db7f181dd3166af6f25d8307ec8378ca923613
status: current
---

# GET /api/roles/person/{person_id}/permissions

## Purpose

Retrieves the aggregated list of roles and permissions for a specific person. It calculates the union of all permissions across all roles assigned to the user to provide a flattened view of their access level. This is used by the web UI to determine feature visibility and administrative capabilities for a specific user.

## Invariants

- **HTTP Method**: `GET`.
- **Path**: `/api/roles/person/{person_id}/permissions`.
- **Auth**: Requires a user with the `admin.roles.view` permission via `require_permission`.
- **Return Shape**: Returns a `UserPermissionsResponse` containing a `person_id` (string), a sorted list of `roles` (strings), and a sorted list of `permissions` (strings).
- **Error State**: Returns a `404 Not Found` if the `person_id` does not exist in the `Person` table.

## Gotchas

- **Privilege Escalation Protection**: While this endpoint is a read-only view, it is part of the security surface area addressed in commit `33a37a3` ("fix(security): close PII / privilege gaps in roles, finder, directory, media"). Any changes to how roles are aggregated or how permissions are calculated must be checked against the logic in the sibling `POST /assign` endpoint to ensure the view remains consistent with the security model.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.view` permission.
- **Side effects**: Changes to user roles (via the sibling `POST /assign` endpoint) will immediately change the output of this endpoint.

## External consumers

- `concorda-web` (via `rolesApi.getUserPermissions`).
