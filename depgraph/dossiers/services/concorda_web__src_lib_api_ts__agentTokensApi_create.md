---
node_id: concorda-web::src/lib/api.ts::agentTokensApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d0f6ecfaf27707744a2f9904ad0fc790fcf88515ab1b99e516eb9a6b38189944
status: current
---

# agentTokensApi.create

## Purpose

Provides the API interface for managing personal agent tokens (API keys) for the authenticated user. It allows users to generate new tokens via `create`, refresh existing ones via `rotate`, or invalidate them via `revoke`. Use this instead of `directoryApi` when the intent is to manage the user's own credentials rather than searching for other members.

## Invariants

- **Method is `POST`** — The `create` method specifically uses a `POST` request to the `/api/profile/agent-tokens` endpoint.
- **Requires `name`** — The `create` method requires a non-empty string for the token's identifier.
- **Returns `AgentTokenWithSecret`** — Successful creation returns the full object including the raw `token` string, which is only visible at the moment of creation.
- **Uses `fetchApiAuthenticated`** — All methods in this object rely on the authenticated session to pass the bearer token.

## Gotchas

- **Secret visibility** — The `token` field is only present in the response of `create` and `rotate`. Subsequent calls to `list` return `AgentTokenSummary`, which lacks the secret string.
- **Identity context** — Because this hits `/api/profile/`, the tokens created are scoped strictly to the currently authenticated user's profile.

## Cross-cutting concerns

- **Auth**: Depends on `fetchApiAuthenticated` to provide the bearer token.
- **Side effects**: Creating or rotating tokens may be used by external scripts or integrations to maintain access without manual login, but the UI impact is primarily seen in the user's own profile security settings.

## External consumers

- `AgentsPage` in `src/app/members/agents/page.tsx` (via `page.tsx:98`).
