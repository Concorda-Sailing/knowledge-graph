---
node_id: concorda-web::src/lib/api.ts::adminApi.importUsers
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b863d5a8b4c02b54c6dbce536aeba7a37eb30207e5396292b7076a727cd5754
status: current
---

# adminApi.importUsers

## Purpose

Handles the bulk upload of user data via a multipart file upload. It is a specialized administrative tool used to ingest user lists, distinct from the granular `deleteUser` or `changePassword` methods in the same `adminApi` object.

## Invariants

- **Requires `File` object.** The first argument must be a browser `File` instance to be correctly appended to the `FormData`.
- **Uses `POST` method.** The request is sent to `/api/admin/users/import`.
- **Mandatory `on_duplicate` query parameter.** The second argument must be either `"skip"` or `"update"` to determine how the backend handles existing user identifiers.
- **Requires authentication.** The method manually retrieves the token via `getAuthToken()` and injects it into the `Authorization` header.
- **Returns `ImportUsersResult`.** The successful response is parsed as a promise of this specific type.

## Gotchas

- **Manual Error Parsing.** Unlike the `fetchApiAuthenticated` wrapper used by other methods in this file, this function implements its own error handling logic to extract the `detail` field from the JSON response body.
- **Auth Failure Mode.** If `getAuthToken()` returns a falsy value, the function throws a generic `"Not authenticated"` error before even attempting the fetch.

## Cross-cutting concerns

- **Auth**: Uses `getAuthToken()` for the Bearer token.
- **Side effects**: Successful imports likely trigger downstream updates to user directory counts or search indexes, though the specific UI refresh logic is handled by the caller (`ImportUsersDialog`).

## External consumers

- `ImportUsersDialog` in `concorda-web/src/components/admin/import-users-dialog.tsx`.
