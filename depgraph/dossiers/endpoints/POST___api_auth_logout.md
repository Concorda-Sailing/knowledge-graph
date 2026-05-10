---
node_id: POST::/api/auth/logout
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6e57876dd646cd2302d2baf56f9bd2e63f727d499e3793e91f313601606252b4
status: current
---

# POST /api/auth/logout

## Purpose

Invalidates the current user's session by deleting their associated token from the database. This is the primary mechanism for a client to end an authenticated session. It is distinct from a simple client-side state clear; it performs a server-side deletion of the `AuthToken` record to ensure the token cannot be reused.

## Invariants

- **HTTP Method is `POST`**.
- **Expects `Authorization` header**. The function looks for the `Authorization` header to identify the token to be revoked.
- **Token is SHA-256 hashed**. The input string is hashed via `hashlib.sha256` before the database lookup to match the stored `token_hash`.
- **Returns a success message**. On successful deletion or if no token is provided, it returns a JSON object with a `"message"` key.

## Gotchas

- **Bearer prefix handling**: The function manually strips the `"Bearer "` prefix (the first 7 characters) if present. If a client sends a raw token without the prefix, the logic still attempts to hash and delete it.
- **Idempotency on missing tokens**: If no `Authorization` header is provided, the function returns `{"message": "No token provided"}` rather than a 401 or 403 error.
- **Manual token hashing**: The database lookup relies on the client-side or middleware-provided token being the raw string that, when hashed, matches the `AuthToken.token` field.

## Cross-cutting concerns

- **Auth**: Directly manages the lifecycle of the `AuthToken` record used by the authentication system.
- **Rate limit**: None explicitly defined for this endpoint, but it is part of the `auth` router subject to general API rate-limiting-related fixes (see commit `ec53704`).
- **Side effects**: Effectively terminates the session for the user, which will cause subsequent authenticated calls (like those using `ApiClient` in tests) to fail.

## External consumers

- `concorda-web::src/lib/api.ts::authApi.logout` (Direct dependency).
