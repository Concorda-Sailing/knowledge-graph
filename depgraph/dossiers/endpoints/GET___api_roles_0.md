---
node_id: GET::/api/roles/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c93acb9a0bb5441c609b015f9f7c47e3f3fa7cbd12c9d79a87ff8e81a349f365
status: llm_drafted
---

# GET /api/roles/{role_name}

## Purpose

Fetches the detailed configuration of a specific role, including its associated permissions. This endpoint is used by the admin dashboard to display role details and by the permission management UI to allow administrators to view what a role is capable of doing. It is distinct from the list-all-roles endpoint, which provides a high-level overview of all available roles.

## Invariants

- **Path parameter `role_name` is a string.** The lookup is performed against the `Role.name` field.
- **Returns a `RoleWithPermissionsResponse`.** This includes the role's metadata and the list of associated `Permission` objects.
- **Requires `admin.roles.view` permission.** Access is guarded by the `require_permission` dependency.
- **Returns 404 if the role does not exist.** The lookup uses `.first()` on the name filter; if no match is found, a `404 Not Found` is raised.

## Gotchas

- **Privilege escalation protection.** Per commit `33a37a3`, the system enforces a strict hierarchy. While this is a `GET` endpoint, any logic that might lead to an update (like the sibling `PUT` endpoint) must respect that an actor cannot edit a role with a higher `level` than their own `actor_max`.
- **Role name vs. ID.** The endpoint identifies roles by `role_name` (string) rather than a numeric ID. Ensure the frontend is passing the string identifier (e.g., `"admin"`) and not a database primary key.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.view` permission via `require_permission`.
- **Rate limit**: None.
- **Audit**: N/A.
- **Side effects**: N/A.

## External consumers

- `concorda-web` (via `rolesApi.get` in `api.ts`).
