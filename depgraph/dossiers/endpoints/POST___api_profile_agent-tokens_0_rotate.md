---
node_id: POST::/api/profile/agent-tokens/{0}/rotate
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2ba9df582f563b1e39290fd98cc47d4e94c9fb101fe3d56ba898f8f7dde1e0a4
status: current
---

# POST /api/profile/agent-tokens/{token_id}/rotate

## Purpose

Generates a new plaintext secret for an existing `AgentToken` and updates the database record. This is used to replace compromised or expiring tokens without deleting the token identity itself. It is distinct from `revoke_token`, which destroys the record, whereas this method preserves the `id` and `scope` but resets the `token_hash`, `created_at`, and `expires_at` timestamps.

## Invariants

- **Method is POST** and requires a valid `token_id`.
- **Requires `require_session_auth`** — the `current_user.id` must match the `person_id` of the token being rotated.
- **Returns `AgentTokenWithSecret`** — the response body includes the new `token` (plaintext) which is required for the client to actually use the new credential.
- **Resets lifecycle metadata** — `last_used_at` and `revoked_at` are explicitly set to `None` during rotation.

## Gotchas

- **`_generate_token()` side effect** — this internal helper generates both the raw string and the hashed version; the raw string is only available in this response. If the client fails to capture the `token` field from this specific response, the new token is lost forever.
- **`DEFAULT_EXPIRY_DAYS` dependency** — the new `expires_at` is calculated relative to `now` using this constant.

## Cross-cutting concerns

- **Auth**: Uses `require_session_auth` to ensure the user owns the token via `AgentToken.person_id == current_user.id`.
- **Audit**: No explicit audit log entry is written in this function, though the `created_at` timestamp is updated.
- **Side effects**: Rotating a token effectively invalidates the previous plaintext string, which will cause any external agent/script using the old string to fail on its next request.

## External consumers

- `concorda-web::src/lib/api.ts::agentTokensApi.rotate`
