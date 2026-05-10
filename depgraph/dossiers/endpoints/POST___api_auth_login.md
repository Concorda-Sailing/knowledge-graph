---
node_id: POST::/api/auth/login
node_kind: endpoint
feature: auth
last_reviewed: 2026-05-09
last_reviewed_against_hash: 008c18dcf9f2206ce5df4598a35f0608413f8a6734605e4c39603ad265c7a6da
status: current
---

# POST /api/auth/login

## Purpose

Trade an email + password for a bearer token. The single front door for credential-based authentication. Sets the auth cookie / token used by every subsequent authenticated request, and is itself the gateway to most of the app's user-visible flows.

Returns `{access_token: str, token_type: "bearer"}` on success. Failures return a structured `detail` object with `code`, `message`, `remaining_attempts`, and `password_reset_clears_lockout` so the frontend can render a specific message rather than a generic "401."

## Invariants

- **Email matching is case-insensitive.** Mobile keyboards default to lowercase but desktop autocomplete may capitalize the local part ("JHill245@gmail.com"). The query uses `func.lower(Person.email) == request.email.strip().lower()`. Do not "tighten" this back to a case-sensitive match — it would break a real population of users silently.
- **Existence is not leaked by ordering.** The deactivated-account check (`leave_date is not None`) runs **after** password verification, so an attacker can't learn that an email is deactivated by timing or status code. Don't reorder.
- **Password rehash is lazy.** If the stored hash is legacy SHA-256 (`_needs_rehash`), a successful login upgrades it to bcrypt and commits. Never remove this — the migration to bcrypt is incremental and depends on every legacy user logging in once.
- **Rate limiter is per-IP, in-memory.** Per memory `feedback_rate_limiter_single_worker`, the in-memory dict in `auth.py` is correct only for `--workers 1`. Adding a worker silently halves the effective rate-limit window. Do not deploy more workers without moving the limiter to Redis.
- **Successful login resets the IP's failure bucket.** Legitimate users who eventually got their password right are not penalized for prior failures.
- **OAuth users have `password_hash = None`.** Oauth-only accounts must never reach this endpoint (oauth has its own route). If they do, the `not user.password_hash` guard returns 401 — correct, but the message "Invalid email or password" is technically misleading. Don't fix this without considering account-existence-leak implications.

## Gotchas

- **The detail object's shape is part of the de-facto contract.** Web parses `detail.code` and `detail.remaining_attempts`. Older shipped iOS builds parse `detail.message`. Adding fields is safe; renaming is a release-coordination problem.
- **`request.state.alert_already_recorded = True`** on lockout suppresses the activity middleware's own logging so the alert isn't double-counted. If you change middleware ordering, verify this still holds.
- **Lockout is lifted by password reset.** The 429 detail explicitly tells the user this so they have a non-time-based recovery path. Do not change without updating the message.
- **`_RATE_LIMITS_DISABLED` skips ALL rate-limiting.** Used in tests. Make sure CI sets it; production must not.
- **`cleanup_expired_tokens(db)` runs on every login.** This is a small per-request cost but it is opportunistic GC. If you remove it, set up a cron to compensate.

## Cross-cutting concerns

- **Auth:** Issues the bearer token consumed by every other endpoint via `Authorization: Bearer <token>`.
- **Activity log:** Lockout 429s and 401s generate `record_status` alerts (with the attempted email).
- **Stripe / Memberships:** Login does not check membership state — that's per-feature. Don't add a membership gate here without coordinating with the existing free-account flow.
- **TOS gate:** Login does not check `tos_accepted_at`; web `/login` redirects to `/policies/accept` on the next authenticated request if needed.

## External consumers

- **Web** `concorda-web::src/lib/api.ts::authApi.login`
- **Test** `concorda-test::lib/api-client.ts::ApiClient.login` (35 transitive test consumers via `api.login(...)` calls)
- **Concorda iOS app**: every shipped build calls this endpoint at startup. The response shape `{access_token, token_type}` is part of the de-facto API contract — do not rename either field.
- **Stripe / OAuth**: not direct consumers but adjacent: changes here affect every authenticated flow downstream.

## Open questions

- The in-memory rate limiter blocks horizontal scaling. Move to Redis before deploying with `--workers > 1`.
- Should we add WebAuthn / passkey support? Today only email+password and Google OAuth are supported.
