---
node_id: concorda-web::src/lib/api.ts::agentTokensApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c9ad15cec6cc92bdad238bf462795ea7c578ed57c61aa4dd35adcebd820f4d56
status: current
---

# agentTokensApi.list

## Purpose

Provides a programmatic interface for managing and viewing the user's API agent tokens. It allows the client to list existing tokens, create new ones with a name, rotate existing tokens for security, and revoke them. This is the primary interface for users to manage their programmatic access credentials within the web UI.

## Invariants

- **Uses `fetchApiAuthenticated`** — All calls require a valid bearer token to access the `/api/profile/agent-tokens` endpoint.
- **Returns `AgentTokenSummary[]`** — The `list` method returns an array of objects containing metadata like `last_used_at` and `revoked_at`, but does *not* include the raw token string.
- **`create` requires a `name`** — The payload must be a JSON-stringified object with a `name` property.
- **`rotate` returns the new secret** — Unlike `list`, the `rotate` method returns an `AgentTokenWithSecret` which includes the new `token` string.

## Gotchas

- **The `list` method is safe, but `rotate` is destructive to the old secret** — Because `rotate` returns the new `token` string, any client calling it must ensure the new secret is immediately captured and stored (e.g., in a copy-to-clipboard UI state), or the old token is lost and the new one is inaccessible.

## Cross-cutting concerns

- **Auth**: Requires `fetchApi-authenticated` context.
- **Audit**: N/A.
- **Side effects**: Used by `AgentsPage` to manage the display of programmatic credentials.

## External consumers

None known.
