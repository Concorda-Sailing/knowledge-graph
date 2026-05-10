---
node_id: GET::/api/roles/person/{0}/roles
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bfc4a2345f7a02e1a6122181de6cf146d3665d12489644b44a0dc4c3b08a030a
status: current
---

# GET /api/roles/person/{person_id}/roles

## Purpose

Retrieves the list of roles assigned to a specific person. This endpoint is used by administrative interfaces to display a user's current access levels and is a prerequisite for any UI that needs to show a user's identity within an organization. It is distinct from `/api/person/{id}/permissions`, which returns the aggregated permission set rather than the specific role objects.

## Invariants

- **HTTP Method is GET.**
- **Requires `admin.roles.view` permission.** Access is guarded by `require_permission("admin.roles.view")`.
- **Returns a list of `UserRoleResponse` objects.** Each object includes `id`, `person_id`, `role_name`, `role_display_name`, and `organization_id`.
- **`assigned_at` is an ISO 8601 string.** If the timestamp is null, the field returns `null`.
- **Returns 404 if the `person_id` does not exist.** The function explicitly checks for the existence of the `Person` object before querying roles.

## Gotchas

- **PII/Security Gap:** Per commit `33a37a3`, this endpoint and its neighbors were part of a security hardening effort to close PII and privilege gaps. Ensure that any changes to the returned fields do not inadvertently expose sensitive user data or bypass the `admin.roles.view` requirement.

## Cross-cutting concerns

- **Auth**: Guarded by `require_permission("admin.roles.view")`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by administrative views to display user identity and access levels.

## External consumers

- `concorda-web` (via `rolesApi.getUserRoles`)
