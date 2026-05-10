---
node_id: concorda-api::models/auth_token.py::AuthToken
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b36197754c03ddffa78efb53d4e456ec69fa7efc093e8f6de55dbb6a56546f1e
status: current
---

# AuthToken

## Purpose

Backend SQLAlchemy model for short-lived session bearer tokens — the credential a logged-in member's browser/Expo client sends as `Authorization: Bearer …` on normal authenticated requests. `routers/auth.py::create_token` generates a 32-byte urlsafe random string, returns the **plaintext** to the client exactly once, and stores only `sha256(plaintext)` in the `token` column. Lifetime is 24h by default and 30d when the login request set `remember_me`. This row is the counterpart to `AgentToken` (long-lived, `cga_`-prefixed, programmatic): `get_current_user_id` routes by prefix — anything without `cga_` is looked up here. If you're touching session auth, login/logout flows, or password reset invalidation, this table is the contract.

## Invariants

- `token` stores `sha256(plaintext_hex)` — 64 chars in practice though the column is `String(128)`. Plaintext is never persisted; a DB leak does not yield usable sessions.
- `token` is unique and indexed; lookups in `get_current_user_id` and `logout` are by hash equality, not by `id`.
- Expiry is **enforced on read**, not by a scheduled job. `get_current_user_id` deletes the row inline when `now > expires_at`; `cleanup_expired_tokens` exists but isn't wired to a cron — expired rows accumulate until someone tries to use them.
- `expires_at` is required at insert and is naive UTC (`datetime.utcnow()`), like the rest of the codebase. Compare against `datetime.utcnow()`, not local time.
- `is_remember_me` is informational; the actual lifetime is baked into `expires_at` at create time. Flipping the boolean post-hoc changes nothing.
- No FK to `Person`. `person_id` is a plain indexed String(36); deleting a Person does **not** cascade-delete their auth tokens (compare AgentToken, which cascades).

## Gotchas

- Password reset (`POST /api/auth/reset-password`) bulk-deletes every row for the user to force re-login on all devices. There is no per-session revoke beyond logout — and logout only kills the bearer that called it.
- No FK + no cascade means orphan rows are possible if a Person row is ever hard-deleted. The expiry-on-read path will still GC them once their TTL passes, but they linger until then.
- The analytics "active sessions" metric (`GET /api/analytics/summary`) counts rows with `expires_at > now()` — because expired rows are only cleaned on access, this overcounts until users actually try to use the stale tokens. It is a ceiling, not a true active count.
- `logout` is a no-op if the bearer doesn't match a row (e.g. already expired and lazy-deleted, or an agent token). It always returns 200.
- Token rotation does not exist — login mints a new row each time; old `remember_me` rows stick around for up to 30 days unless explicitly logged out or password-reset.
- Only two commits have touched this file (initial scaffold + the big event-management drop); there is essentially no rollback history to mine.

## Cross-cutting concerns

- **Auth split:** session tokens (this table) vs. agent tokens (`agent_tokens`) share the `Authorization: Bearer …` header; routing is by `cga_` prefix in `routers/auth.py::get_current_user_id`. Adding a new bearer kind means another branch there.
- **Side effect on every request:** unlike AgentToken, this path does **not** bump a `last_used_at` — so authenticated reads are pure SELECT, no write transaction. Don't add a `last_used_at` here without considering the read-replica/rate-limit implications that motivated the AgentToken note.
- **Password reset blast radius:** resetting a password nukes all sessions for that user system-wide. Intentional, but worth knowing before changing the reset flow.
- **Rate limits:** login endpoints are governed by the in-memory limiter (single-worker constraint — see the rate-limiter memory note). The token table itself has no per-row throttle.
- **No audit/event:** create, expire-on-read, logout, and bulk-delete on password reset emit no notifications, no error_log rows, no websocket events.

## External consumers

- The Concorda web app (`concorda-web`) and the Expo iOS client — both store the plaintext bearer client-side and send it on every authenticated call.
- E2E test harness (`concorda-test`) authenticates the same way.
- None known beyond first-party clients. There is no third-party OAuth surface that consumes these tokens.

## Open questions

- Should expired rows have a periodic sweep? `cleanup_expired_tokens` is defined but uncalled; analytics "active sessions" would become accurate if it ran on a schedule.
- Should `person_id` become a real FK with cascade, to match AgentToken and prevent orphans?
- Should remember-me sessions get a sliding window (bump `expires_at` on use) rather than a fixed 30 days from login?
- Is there value in a `last_used_at` for security forensics (detect dormant sessions / stolen-laptop scenarios), accepting the per-request write cost?
- Should `logout` also accept a "log out everywhere" flag that does what password-reset does today?
