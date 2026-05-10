---
node_id: concorda-api::models/account_setup_token.py::AccountSetupToken
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ffb3adef2bc6a3423c51e35cfa069d3fec41f5614e3bb0e798031d31d175235a
status: current
---

# AccountSetupToken

## Purpose
Backend SQLAlchemy model for one-time tokens used to set up a newly-created account — verifying email and setting an initial password. A token is minted whenever an account is created without a password (admin invite, free signup needing email verification, or `resend-setup-email`), emailed to the user as a URL parameter, and consumed by one of four `/api/auth` endpoints. Single-use, time-limited (72h), and stored as the SHA-256 hash of the raw token so a DB read cannot recover usable links. Separate from `PasswordResetToken` even though the table shape is identical — the lifecycle and downstream side effects (sets `email_verified`, sets `password_hash` on first set) differ.

## Invariants
- The `token` column stores `sha256(raw)`, never the raw token. All four consumer routes look up via `_hash_token(token)` — never query by raw value.
- A token is valid only if `used == False` AND `datetime.utcnow() <= expires_at`. Both checks must run on every consume path.
- On successful consume, `used` is flipped to `True` in the same transaction as the user-state mutation (`email_verified`, `password_hash`). Don't split those commits.
- Raw token is returned exactly once, from `create_setup_token`. It is never logged or persisted in plaintext.
- `expires_at` and `created_at` are naive datetimes written via `datetime.utcnow()` — treat them as UTC. Do not introduce `datetime.now()` here.
- `person_id` is a bare `String(36)` — no FK constraint. Code assumes the referenced `Person` may have been deleted and handles the lookup miss with a 400.

## Gotchas
- The table is shared by two distinct flows: pure email verification (`/verify-email` only flips `email_verified`) and full account setup (`/setup-account` also sets `password_hash`). Same model, different consume semantics — don't collapse the endpoints.
- `/resend-setup-email` mass-invalidates prior unused tokens for the person via a bulk `UPDATE ... SET used=True` before minting a new one. If you add columns whose values need updating on invalidation, that bulk update will silently skip them.
- `/verify-email` returns success (`"Email already verified"`) when `used == True`, but `/validate-setup-token` and `/setup-account` return 400 for the same condition. Idempotency is endpoint-specific, not a model-level property.
- No cleanup job — expired/used tokens accumulate forever. Acceptable today (low volume), but a future GDPR/retention pass will need a sweep.
- `email_verified` is set to `True` inside `register` *before* the token is emailed in at least one branch (line 850-851). That looks wrong on its face but is intentional for the paid/invited path; do not "fix" without tracing the call sites.

## Cross-cutting concerns
- Auth: tokens are an unauthenticated bearer to a privileged operation (set password). Treat any change to consume-path validation as a security-sensitive edit.
- Rate limiting: `/resend-setup-email` is rate-limited per-email in-process (see `_resend_setup_rate_limit`); the limiter is single-worker only (see `feedback_rate_limiter_single_worker`). Multi-worker deploys would let an attacker spam setup emails.
- Side effects on consume: flips `Person.email_verified` and (for `/setup-account`) writes `Person.password_hash`. `/setup-account` also mints an auth token via `create_token` for auto-login — changes here affect the post-setup session.
- Disclosure: `/resend-setup-email` returns a constant response regardless of whether the email exists, is throttled, or already has a password. Preserve that.

## External consumers
None known. Tokens are consumed by the Concorda web app's setup/verify pages via the four `/api/auth` routes; no third-party integration, scheduled job, or webhook depends on this model.

## Open questions
- Should expired/used rows be reaped on a schedule, or left for a future retention sweep?
- The model is structurally identical to `PasswordResetToken`. Worth unifying behind a single `OneTimeToken` with a `purpose` enum, or is the semantic split (verify-vs-setup-vs-reset) worth the duplication?
- `person_id` has no FK — intentional (tolerates Person deletion) or oversight? If intentional, a comment on the column would prevent a future migration from "fixing" it.
