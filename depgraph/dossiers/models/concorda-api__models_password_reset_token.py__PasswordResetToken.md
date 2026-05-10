---
node_id: concorda-api::models/password_reset_token.py::PasswordResetToken
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ede4bb62118cd00df5bb67086aec0ff58849088d783c9b2dfe79cf0c7612fe38
status: llm_drafted
---

# PasswordResetToken

## Purpose
Backend SQLAlchemy model for one-time password-reset tokens. A row is minted by `create_reset_token` whenever a user with a known password hits `/api/auth/forgot-password`, emailed to the user as a URL parameter, and consumed by `/validate-reset-token` (preflight) and `/reset-password` (commit). Single-use, time-limited (1 hour — much tighter than `AccountSetupToken`'s 72h), and stored as the SHA-256 hash of the raw value so a DB read can't recover usable links. Structurally identical to `AccountSetupToken` but a deliberately separate table — the consume path only writes `password_hash` and never touches `email_verified`, because possession of a reset link does not prove current control of the email (the row may have been minted before an email change). Three dependents, all in `routers/auth.py`.

## Invariants
- The `token` column stores `sha256(raw)`, never the raw value. All three consumer routes look up via `_hash_token(token)` — never query by raw value.
- A token is valid only if `used == False` AND `datetime.utcnow() <= expires_at`. Both checks must run on every consume path.
- `expires_at` is one hour from creation (`RESET_TOKEN_EXPIRE_HOURS = 1`). Do not loosen this without revisiting the security model — short window is the primary mitigation for link interception.
- On successful `/reset-password`, `used=True`, `Person.password_hash` update, and the bulk delete of `AuthToken` for that user happen in one commit. Don't split that transaction.
- Only users with an existing `password_hash` get a token minted (`/forgot-password` skips passwordless accounts — those go through `AccountSetupToken` instead).
- `expires_at` and `created_at` are naive datetimes written via `datetime.utcnow()` — treat as UTC. Do not introduce `datetime.now()` here.
- `person_id` is a bare `String(36)` — no FK constraint. Consume paths handle the lookup miss with a 400.

## Gotchas
- `/forgot-password` mass-invalidates *all* prior unused tokens for the person via `UPDATE ... SET used=True` before minting the new one. If you add columns whose values must change on invalidation, that bulk update will silently skip them.
- `/reset-password` deletes every `AuthToken` for the user — a successful reset force-logs-out all sessions on all devices. That's intentional ("if someone reset your password, kill any session they might've stolen"); don't soften it.
- Lockout clearing only happens on `/reset-password`, not `/forgot-password`. The comment at line 1201-1203 is load-bearing: `/forgot-password` doesn't prove email control, so clearing the lockout there would let an attacker DOS-then-unlock just by requesting a reset.
- `/forgot-password` returns a constant "If an account exists..." message regardless of whether the email exists, has a password, or got rate-limited above the threshold. Preserve the no-disclosure behavior.
- In test mode (`_TEST_MODE_TOKEN_ECHO`), `/forgot-password` echoes the raw token in the response so E2E specs can skip the email round-trip. That flag must never be true in production.
- Per-IP rate limit (3/hour) lives in an in-process `defaultdict` — single-worker only (see `feedback_rate_limiter_single_worker`). Multi-worker deploys would let an attacker spam reset emails.
- No cleanup job — expired/used rows accumulate forever.

## Cross-cutting concerns
- Auth: tokens are unauthenticated bearers to a privileged operation (overwrite password). Any change to consume-path validation is security-sensitive.
- Rate limits: `/forgot-password` is IP-throttled at 3/hour via `_reset_rate_limit`; bypass-able under multi-worker.
- Audit: `/forgot-password` writes a `NotificationLog` row (event_type `auth.password_reset`, status `sent`/`failed`) and on failure calls `services.error_alerts.record_email_failure`. `/reset-password` writes no audit row of its own today — the only trail of a completed reset is the `used=True` flip plus the wiped `AuthToken` rows.
- Side effects on consume: writes `Person.password_hash`, bulk-deletes `AuthToken` for the user, clears the per-IP login lockout. Does *not* touch `email_verified`.

## External consumers
None known. Tokens are consumed by the Concorda web app's reset-password page via the three `/api/auth` routes; no third-party integration, scheduled job, or webhook depends on this model.

## Open questions
- Worth unifying with `AccountSetupToken` behind a single `OneTimeToken` with a `purpose` enum? The shapes match, but the consume semantics (which Person columns get written, what gets invalidated alongside) diverge enough that the duplication may be the honest representation.
- Should a successful reset emit its own audit row (e.g. `NotificationLog` or a dedicated security event) instead of relying on `used=True` + `AuthToken` deletion as the only trail?
- Should expired/used rows be reaped on a schedule?
