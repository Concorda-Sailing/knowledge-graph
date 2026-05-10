---
node_id: concorda-web::src/lib/api.ts::agentTokensApi.revoke
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 681755215545a4fba703c5890a487d87c3ed9f4454f4515695a7eeb9f5abb6c9
status: llm_drafted
---

# agentTokensApi.revoke

## Purpose

The method to invalidate a specific agent token via the API. It targets a specific token ID and performs a `DELETE` request to the `/api/profile/agent-tokens/{id}` endpoint. Use this when an agent needs to manually terminate a session or a specific device's access.

## Invariants

- **Method is `DELETE`** — must use the DELETE verb on the specific resource path.
- **Requires `fetchApiAuthenticated`** — the request must include the current user's bearer token to authorize the revocation of their own or managed tokens.
- **Returns `void`** — the API response body is empty upon successful revocation.

## Gotchas

- **Identity-based access** — because it uses `fetchApiAuthenticated`, the caller must have the appropriate permissions to revoke the specific token ID provided; failing to handle a 403/401 gracefully in the UI will result in a silent failure or a generic error state.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is tied to an authenticated session.
- **Side effects**: Revoking a token will immediately invalidate any active sessions or client-side state relying on that specific token ID.

## External consumers

- `AgentsPage` in `src/app/members/agents/page.tsx` (via `page.tsx:126`).
