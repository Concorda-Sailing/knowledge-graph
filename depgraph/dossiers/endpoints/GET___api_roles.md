---
node_id: GET::/api/roles
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 11e9fda285f3d2c2e0cbbd2a37f80ba1ef177bd4d1cbdcde9cf05d0e15ed1b67
status: current
---

# GET /api/roles

## Purpose

Provides a list of all available roles in the system, ordered by their hierarchy level. This is a read-only endpoint used by administrative interfaces to display the current role structure. Use this when you need to populate dropdowns or lists of roles for user assignment or system-wide auditing.

## Invariants

- **HTTP Method is `GET`**.
- **Requires `admin.roles.view` permission** via the `require_permission` dependency.
- **Returns a list of `RoleResponse` objects.**
- **Ordering is strictly enforced** by `Role.level` to ensure the hierarchy is visible in the UI.

## Gotchas

- **Security/PII sensitivity:** Per commit `33a37a3`, this endpoint and its siblings are part of the hardened security layer to close PII and privilege gaps. Ensure that any changes to the returned `RoleResponse` do not inadvertently expose sensitive user-level data.
- **Hierarchy-based access:** While this specific endpoint is a simple list, it is part of the same router logic that implements the "block privilege escalation" check (seen in the sibling `PUT` method) to prevent users from editing roles with a higher `level` than their own.

## Cross-cutting concerns

- **Auth**: Requires `admin.roles.view` permission.
- **Audit**: N/A.
- **Rate limit**: None.

## External consumers

- `concorda-web::src/lib/api.ts::rolesApi.list` (via `http_call`)
