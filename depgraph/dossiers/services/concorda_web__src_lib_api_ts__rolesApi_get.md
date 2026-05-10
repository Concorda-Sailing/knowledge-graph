---
node_id: concorda-web::src/lib/api.ts::rolesApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f652e255d7d40afca76d245344f1ebf46be5666ef71b94c82079ccf201af89f2
status: llm_drafted
---

# rolesApi.get

## Purpose

Fetches the detailed permission set and metadata for a specific role by name. This is the primary method for retrieving the full `RoleWithPermissions` object, which is required for the admin role-management interfaces. Use this instead of `list()` when you need to inspect the specific permissions assigned to a single role.

## Invariants

- **Requires a valid `name` string** as the URL segment for the endpoint.
- **Uses `fetchApiAuthenticated`** — the request must include a valid bearer token.
- **Returns a `RoleWithPermissions` object** containing the role's identity and its associated permission set.
- **Endpoint path is `/api/roles/${name}`**.

## Gotchas

- **Role name sensitivity**: The `name` parameter is used directly in the URL path; ensure the string matches the exact identifier expected by the backend to avoid 404s.
- **Dependency on `fetchApiAuthenticated`**: If the authentication layer fails or the token is missing, this will throw an error before the request is even dispatched.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has administrative privileges to view role details.
- **Side effects**: Changes to roles via this endpoint (or its sibling `updatePermissions`) will affect the authorization logic across the entire platform, specifically impacting access control for the `RolesContent` page and `RoleDialog`.

## External consumers

- `concorda-web::src/app/members/admin/roles/page.tsx` (RolesContent)
- `concorda-web::src/components/admin/role-dialog.tsx` (RoleDialog)
