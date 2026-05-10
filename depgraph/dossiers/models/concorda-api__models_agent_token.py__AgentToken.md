---
node_id: concorda-api::models/agent_token.py::AgentToken
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 20078574cd0eee9d56132c70fddad8b59d7c5da057777960d63847864a0cfddd
status: current
---

# AgentToken

## Purpose

Backend SQLAlchemy model for long-lived agent/API tokens (sha256-hashed, scope-bound). Persists bearer credentials that LLM agents and other programmatic clients use to call the API on a member's behalf, distinct from short-lived session JWTs stored in `auth_tokens`. The plaintext token (prefix `cga_`) is shown to the user exactly once at create/rotate time; only the SHA-256 hex digest lives in the DB, so a leak of this table does not yield usable tokens. `routers/auth.py::get_current_user_id` distinguishes session vs. agent tokens by the `cga_` prefix and routes lookups here, bumping `last_used_at` on every successful resolution. A future Claude touching this model should assume the row schema is the contract for both the management endpoints in `routers/agent_tokens.py` and the bearer-auth path in `routers/auth.py`.

## Invariants

- `token_hash` stores sha256 hex of the full plaintext (including the `cga_` prefix) — 64 chars, unique. Plaintext is never stored.
- `person_id` cascades on delete: removing a Person deletes their tokens. Tokens are always scoped to one person; there are no org-level agent tokens.
- A token is "active" iff `revoked_at IS NULL AND expires_at > now()`. Hard cap of 5 active tokens per person (`MAX_ACTIVE_TOKENS` in the router).
- Default lifetime is 183 days (~6 months) from creation; `expires_at` is non-null and required at insert.
- `scope` defaults to `"read"` and is the only value v1 uses. The read-only contract is currently enforced by HTTP method, not by inspecting this column.
- Timestamps are written with `datetime.utcnow()` (naive UTC), matching the rest of the codebase — they are stored as naive-as-UTC and should be read/compared with `datetime.utcnow()`, not local time.

## Gotchas

- Read-only enforcement lives in **two** places and neither one consults `scope`: a global middleware in `main.py` (prefix sniff on `Bearer cga_`) and `require_session_auth` in `auth_middleware.py`. Adding a `"write"` scope value will not unlock writes — you must also relax the middleware. Conversely, renaming the `cga_` prefix silently disables both gates.
- Rotate is destructive in place: it overwrites `token_hash`, resets `created_at`, `expires_at`, `last_used_at`, **and clears `revoked_at`**. Rotating a revoked token resurrects it. No audit row is written.
- DELETE on this resource is a hard row delete, not a soft revoke — once gone, you cannot inspect `last_used_at` for forensics. The `revoked_at` column exists but the management router never sets it (rotate clears it, delete bypasses it).
- The 5-token cap is checked at create time only; it does not account for tokens about to expire, and rotate ignores the cap entirely (it operates on an existing row).
- `name` is required but not unique per person — duplicate labels are allowed.
- Only one commit has ever touched this file (`cdf2594`); there is no rollback history to mine, which means edge cases here are unproven in production.

## Cross-cutting concerns

- **Auth split:** session tokens (`auth_tokens`) and agent tokens (this table) share the `Authorization: Bearer …` header; routing is by `cga_` prefix in `routers/auth.py::get_current_user_id`. Management endpoints (`/api/profile/agent-tokens/*`) intentionally require `require_session_auth`, so an agent token cannot mint or rotate another agent token.
- **Side-effect on every API call:** successful agent-token resolution writes `last_used_at` and commits — every authenticated agent request incurs a write transaction. Worth remembering when reasoning about read-replica routing or rate-limit windows.
- **No audit/event:** create, rotate, revoke, and delete emit no notifications, no error_log rows, and no websocket events. If audit becomes a requirement, this is the seam.
- **Rate limits:** none specific to this resource; inherits whatever global limiter applies to `/api/profile/*`. Remember the existing limiter is single-worker-only (see memory note on rate limiter).

## External consumers

- The Concorda member portal skill (`concorda-portal`) and other Claude-agent integrations that authenticate as a member via `cga_*` bearer tokens.
- None known beyond first-party agent tooling; there is no public OAuth/app-registration surface and no documented third-party integration.

## Open questions

- Should `scope` actually be load-bearing in v2 (e.g., `read`, `write:profile`, `write:crew`) instead of the current prefix-and-method hack? If so, the two enforcement points in `main.py` and `auth_middleware.py` need to consult the row, which means a DB lookup on every request rather than a string-prefix check.
- Should DELETE soft-revoke (set `revoked_at`) instead of hard-deleting, to preserve `last_used_at` for forensics?
- Should rotate refuse to operate on a revoked row, or is "rotate as un-revoke" intentional?
- Is the 5-active cap the right ceiling now that one human may run several distinct Claude agents in parallel?
