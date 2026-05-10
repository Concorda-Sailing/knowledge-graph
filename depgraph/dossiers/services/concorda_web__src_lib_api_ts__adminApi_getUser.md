---
node_id: concorda-web::src/lib/api.ts::adminApi.getUser
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b7293e28e49f05b52af1a00e95031c283acf7173e94b524c264a4dea2d8ea5ab
status: current
---

# adminApi.getUser

## Purpose

Fetches detailed user information by a specific user ID. This is a read-only operation used by administrative interfaces to display user profiles or verify identity details. It is distinct from `createUser` or `updateUser` which handle state changes; `getUser` is the primary method for retrieving a single user's current state.

## Invariants

- **Method is GET** — Performs a standard authenticated GET request.
- **Path requires `id`** — The endpoint is `/api/admin/users/${id}`.
- **Returns `UserDetails`** — The response shape is defined by the `UserDetails` type.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the request includes the necessary bearer token.

## Gotchas

- **Requires Admin privileges** — Because this uses `fetchApiAuthenticated` and hits an `/api/admin/` route, the caller must have an active session with administrative permissions.
- **Direct dependency for User Dialogs** — The `UserDialog` component in `user-dialog.tsx` relies on this to populate user details; any change to the return shape of `UserDetails` will break the administrative UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin session).
- **Side effects**: Used by the `UserDialog` component to display user-specific data.

## External consumers

None known.
