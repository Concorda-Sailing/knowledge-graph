---
node_id: POST::/api/profile/agent-tokens
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b9f4eaf1d566f2068c1602bd143ee3e49cf3d9195336e4a9aab7c0d251564ac
status: current
---

# POST /api/profile/agent-tokens

## Purpose

Generates a new long-lived bearer token for a user's automated processes (e.g., external scripts or integrations). This endpoint is distinct from standard session authentication; it creates a `AgentToken` record with a `read` scope and a specific expiration. Use this when a user needs to authorize a non-interactive client to access their profile data.

## Invariants

- **HTTP Method**: `POST`.
- **Auth**: Requires a valid session via `require_session_auth`.
- **Response Shape**: Returns `AgentTokenWithSecret`, which includes the plaintext `token` string.
- **Token Scope**: Hardcoded to `"read"` at creation.
- **Expiration**: Sets `expires_at` to `now + DEFAULT_EXPIRY_DAYS`.
- **Identity**: The `person_id` is strictly tied to the `current_user.id`.

## Gotchas

- **Strict Token Limit**: The `_active_count` check prevents users from creating infinite tokens. If `_active_count(db, current_user.id) >= MAX_ACTIVE_TOKENS`, the request fails with a 400 error.
- **Rotation Resets Metadata**: Calling the `/rotate` endpoint (see `rotate_token`) resets `last_used_at` and `revoked_at` to `None` and updates the `created_at` timestamp to the current time.
- **Plaintext Exposure**: The `token` field is only available in the response of this `POST` call (and the rotation call). Subsequent `GET` requests to list tokens will only see the `AgentTokenSummary` (which lacks the secret).

## Cross-cutting concerns

- **Auth**: Uses `require_session_auth` to ensure the user is logged in before allowing token generation.
- **Side effects**: Creates a record in the `AgentToken` table, which is used by external consumers to authenticate against the API.

## External consumers

- `concorda-web::src/lib/api.ts::agentTokensApi.create` (via `http_call`).
- External automated agents/scripts using the generated bearer token.
