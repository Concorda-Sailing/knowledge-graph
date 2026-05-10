---
node_id: GET::/api/profile/agent-tokens
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 27e894b295d809935134c7e3a39e64a8b3fdc3e3e6a4ddcd197d8b4616cc8d40
status: llm_drafted
---

# GET /api/profile/agent-tokens

## Purpose

Retrieves a list of all active or expired agent tokens associated with the authenticated user. This endpoint is used by the web UI to display the user's current "API keys" or "Agent Tokens," allowing them to view metadata like creation date and expiration without exposing the raw secret. It is distinct from the `POST` endpoint which creates the tokens and the `rotate` endpoint which regenerates them.

## Invariants

- **Auth requirement**: Requires a valid session via `require_session_auth`.
- **Ownership constraint**: Only returns tokens where `AgentToken.person_id` matches the `current_user.id`.
- **Return shape**: Returns a `list[AgentTokenSummary]`. This summary type excludes the raw `token` string to prevent accidental exposure of secrets in the UI.
- **Ordering**: Results are returned in descending order by `created_at`.

## Gotchas

- **Token limit enforcement**: While this is a `GET` endpoint, it is tightly coupled to the `MAX_ACTIVE_TOKENS` logic found in the `POST` method. If a user attempts to create a new token via the sibling `POST` endpoint, they must first use this list to identify and revoke an existing one.

## Cross-cutting concerns

- **Auth**: Depends on `require_session_auth` to ensure the user can only see their own tokens.
- **Side effects**: Used by the agent token management UI to populate the list of available keys.

## External consumers

- `concorda-web::src/lib/api.ts::agentTokensApi.list`
