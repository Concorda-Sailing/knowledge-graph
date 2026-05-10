---
node_id: concorda-web::src/lib/api.ts::agentTokensApi.rotate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dfe3a24169976559dcd11afac2b1521bc1b052390680077b265be731e8b4b9c2
status: current
---

# agentTokensApi.rotate

## Purpose

Triggers a rotation of a specific agent's secret token via the API. This is used when a user needs to refresh the credentials for an automated agent or when a security event necessitates a credential change. It is distinct from `revoke`, which destroys the token, and `create`, which generates a new one from scratch.

## Invariants

- **HTTP Method is `POST`** — The rotation is a state-changing operation on a specific resource ID.
- **Endpoint path is `/api/profile/agent-tokens/${id}/rotate`** — The `id` must be the unique identifier for the specific agent token being rotated.
- **Returns `AgentTokenWithSecret`** — A successful rotation returns the new token and its associated secret, allowing the UI to display or copy the new credentials immediately.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the caller has the necessary permissions to manage agent tokens.

## Gotchas

- **Requires `fetchApiAuthenticated`** — Since this is a profile-level operation, the user must be authenticated and authorized to manage these specific tokens.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is tied to a valid user session.
- **Side effects**: Rotating a token will invalidate the previous secret, potentially breaking any external scripts or automated processes currently using the old token.

## External consumers

None known.
