---
node_id: DELETE::/api/profile/agent-tokens/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d22201df3d6b4a9472dfa2f6816cf52ade60c1124284565cb15eebe4de922d09
status: current
---

# DELETE /api/profile/agent-tokens/{token_id}

## Purpose

Revokes a specific agent-side access token. It is used to invalidate long-lived tokens used by automated agents or integrations. Unlike a global session revocation, this targets a specific `token_id` associated with the `current_user`.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `require_session_auth`**. The caller must have a valid session to revoke an agent token.
- **Returns `204 No Content` on success.**
- **Strict Ownership Check.** The query filters by both `token_id` and `current_user.id`, ensuring a user can only delete their own tokens.

## Gotchas

- **`404 Not Found` is ambiguous.** If the `token_id` exists but belongs to a different user, the API returns a 404 rather than a 403. This is intentional to prevent token enumeration/discovery via error messages.

## Cross-cutting concerns

- **Auth**: Requires `require_session_auth` (session-based authentication).
- **Audit**: N/A.
- **Side effects**: Revoking a token will immediately invalidate any subsequent requests made by the agent using that specific token.

## External consumers

- `concorda-web::src/lib/api.ts::agentTokensApi.revoke`
