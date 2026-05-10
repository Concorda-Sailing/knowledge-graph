---
node_id: concorda-web::src/lib/api.ts::rolesApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4e38076857da142806be6f811436ccd281f1eeac41dc6ba80217b96c660b4f33
status: llm_drafted
---

# rolesApi.list

## Purpose

Provides access to the system's role and permission hierarchy. It is used to fetch the full list of available roles, drill down into specific role permissions, and manage the assignment of permissions to roles. Use this when you need to display the administrative role management interface or check the permission structure of a specific user.

## Invariants

- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the request includes a valid bearer token.
- **Returns `Role[]`** — The `list` method returns an array of `Role` objects, which are used to populate the administrative role selection UI.
- **Method-specific payloads** — `updatePermissions` requires a `PUT` method and a JSON-stringified array of permission strings.

## Gotchas

- **Permission-based UI gating** — While this API provides the data, the UI logic for hiding/showing elements based on these roles is handled by the component's consumption of the `RoleWithPermissions` shape.
- **Role-name dependency** — The `get` and `updatePermissions` methods rely on the `name` string as a unique identifier; if the backend changes the naming convention for roles, these calls will fail to find the target.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid session/token).
- **Side effects**: Changes to roles via `updatePermissions` will immediately affect the permission checks in the `RolesContent` page and the `UserDialog` component.

## External consumers

None known.
