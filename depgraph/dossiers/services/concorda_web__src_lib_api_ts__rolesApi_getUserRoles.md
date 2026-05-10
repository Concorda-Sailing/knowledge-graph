---
node_id: concorda-web::src/lib/api.ts::rolesApi.getUserRoles
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dbe68277cc85443bd20c94d9041d244fa84d8c2fb3fd2194650cb4abaaf301ca
status: llm_drafted
---

# rolesApi.getUserRoles

## Purpose

Retrieves the specific roles assigned to a given user via their `userId`. This is a specialized lookup within the `rolesApi` service used to determine a user's authorization level and functional identity (e.g., distinguishing between a standard user and an administrator or owner) within the application.

## Invariants

- **Requires `userId`** — The function accepts a single string representing the unique identifier of the user.
- **Uses `fetchApiAuthenticated`** — This call is subject to the same authentication requirements as other `rolesApi` methods, requiring a valid bearer token.
- **Returns `UserRoleAssignment[]`** — The response is an array of objects mapping the user to their specific roles.

## Gotchas

- **Identity vs. Permissions** — While `getUserRoles` returns the roles themselves, the UI often needs the granular permissions *within* those roles. If you need to check for a specific capability (e.g., "can edit boat"), you may need to combine this with `getUserPermissions` or ensure the role object contains the necessary metadata.
- **Dependency on `fetchApiAuthenticated`** — If the authentication state is lost or the token expires, this will fail with a 401/403, which is handled by the global fetch wrapper.

## Cross-cutting concerns

- **Auth**: Depends on `fetchApiAuthenticated`; requires a valid session/token.
- **Side effects**: Used to drive permission-based UI rendering (e.g., showing/hiding admin controls or owner-specific actions).

## External consumers

None known.
