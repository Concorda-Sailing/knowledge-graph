---
node_id: GET::/api/roles/permissions/all
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3de148dc08d002dd7b478fc416a3969456c7ecec7cb90a244e5884167642c2d8
status: llm_drafted
---

# GET /api/roles/permissions/all

## Purpose

Retrieves the full list of all available permissions within the system. This is a read-only endpoint used to populate administrative interfaces, such as role-creation or permission-assignment forms. It is distinct from `get_user_permissions`, which returns the aggregated permissions for a specific individual.

## Invariants

- **HTTP Method**: `GET`.
- **Auth Requirement**: Requires a user with the `admin.roles.view` permission.
- **Return Shape**: Returns a `list[PermissionResponse]`.
- **Ordering**: Permissions are returned sorted by `Permission.category` and then `Permission.name` to ensure a stable, predictable UI list.

## Gotchas

- **Security/PII Leakage**: Per commit `33a37a3`, this endpoint (and the roles router generally) was recently updated to close privilege gaps. Ensure that any new fields added to the `Permission` model do not inadvertently expose sensitive metadata that violates the "close PII / privilege gaps" fix.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.view` via `require_permission`.
- **Audit**: N/A.
- **Side effects**: Used by the administrative role management UI to display available permission options.

## External consumers

- `concorda-web::src/lib/api.ts::rolesApi.listPermissions`

## Open questions
