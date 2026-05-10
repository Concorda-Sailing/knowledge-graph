---
node_id: concorda-web::src/lib/api.ts::rolesApi.getUserPermissions
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65d7e144b40a8ec4783fa1cfcf3cd617b4de0726fc9d63aec796978a3c662635
status: llm_drafted
---

# rolesApi.getUserPermissions

## Purpose

Fetches the specific permission set for a given user ID. This is a granular lookup used to determine what actions a user is authorized to perform within the application. It is distinct from `getUserRoles`, which returns the high-level role assignments; `getUserPermissions` provides the actual capability strings required for fine-grained UI gating and API authorization checks.

## Invariants

- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the request includes the bearer token.
- **Returns `UserPermissions` shape** — The response is a structured object containing the user's permission strings.
- **Input is a `userId` string** — Expects a valid user identifier to construct the path `/api/roles/person/${userId}/permissions`.

## Gotchas

- **Role vs. Permission distinction** — Recent work on `coowner` logic (e.g., commit `47688ac`) emphasizes that membership (like being a Boat Owner) is a prerequisite for certain actions, but the actual permission check may rely on the granular output of this method.
- **Dependency on `fetchApiAuthenticated`** — If the authentication state is lost or the token is invalid, this will fail via the standard `fetchApiAuthenticated` error handling.

## Cross-cutting concerns

- **Auth**: Dependent on `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Used to drive permission-based UI rendering (e.g., showing/hiding administrative or ownership-related buttons).

## External consumers

None known.
