---
node_id: concorda-web::src/lib/api.ts::adminApi.createUser
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7dedc444484e82d82c3d6d7c1e30cdd1e0cb9c690ddcfc255d26e8ec979d94a2
status: llm_drafted
---

# adminApi.createUser

## Purpose

Creates a new user in the system via a POST request to the admin endpoint. It is a core part of the `adminApi` service used to provision new members. Use this when building administrative interfaces that require programmatic user creation, such as the `UserDialog` component.

## Invariants

- **HTTP Method is `POST`** — The request must use POST to the `/api/admin/users` endpoint.
- **Payload is `CreateUserData`** — The input must be a serialized JSON object matching the `CreateUserData` interface.
- **Returns `UserCreateResponse`** — Successful creation returns the response shape defined by the server.
- **Requires `fetchApiAuthenticated`** — This method relies on the authenticated session/token provided by the underlying fetch wrapper.

## Gotchas

- **Manual Token Handling in Siblings**: While `createUser` uses the standard `fetchApiAuthenticated` wrapper, the sibling `importUsers` in the same object manually extracts the token via `getAuthToken()`. If you are refactoring the auth flow, ensure you check if the pattern is being bypassed in the `adminApi` block.

## Cross-cutting concerns

- **Auth**: Requires a valid admin session via `fetchApiAuthenticated`.
- **Side effects**: Creating a user may trigger downstream effects in the directory or member lists, though the specific UI updates are handled by the component-level state (e.g., `UserDialog`).

## External consumers

- `concorda-web::src/components/admin/user-dialog.tsx::UserDialog`
