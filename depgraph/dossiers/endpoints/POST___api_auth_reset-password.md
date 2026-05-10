---
node_id: POST::/api/auth/reset-password
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ee9cd68aa291e483cbec8fc272c96649a768f66d276573771dc2b40708aa5b0
status: llm_drafted
---

# POST /api/auth/reset-password

## Purpose

Completes the password reset flow by validating a provided token and updating the user's password. This endpoint is the final step in the recovery-of-access flow, transitioning from a temporary `PasswordResetToken` to a permanent `password_hash` on the `Person` record. It is distinct from `/forgot-password` as it performs the actual mutation and identity verification.

## Invariants

- **Method is `POST`** and requires a `ResetPasswordRequest` body containing a `token` and a new `password`.
- **Token must be valid and unexpired.** The function checks `reset_token.token` against a hashed version and verifies `datetime.utcnow() > reset_token.expires_at`.
- **One-time use only.** Upon successful password update, `reset_token.used` is set to `True`.
- **Invalidates existing sessions.** A successful reset triggers a deletion of all existing `AuthToken` records for the associated `user.id` to force a global logout.
- **Returns a success message.** On success, returns `{"message": "Password reset successfully"}`.

## Gotchas

- **Clears login lockout on success.** Per commit `2ef2c99`, a successful password reset calls `_clear_login_lockout` for the client's host. This is a deliberate security/UX trade-off: because the user has proven ownership of the email via the token, we lift the rate-limit/lockout penalty for that IP/host.
- **Case-sensitivity in lookup.** Per commit `9a5db8f`, the system now ensures email-related lookups (including those leading to reset flows) are handled case-insensitively to prevent user confusion during the recovery process.
- **Strict password validation.** The endpoint calls `validate_password(request.password)`; if the new password does not meet complexity requirements, it returns a `400 BAD REQUEST` with the specific error string.

## Cross-cutting concerns

- **Auth**: Does not require a Bearer token, as the `ResetPasswordRequest.token` serves as the temporary authorization.
- **Rate limit**: Triggers `_clear_login_lockout` on success, affecting the rate-limiting state for the client host.
- **Side effects**: Deletes all `AuthToken` entries for the user, effectively logging them out of all devices.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.resetPassword`
- `concorda-web::src/lib/api.ts::authApi.resetPassword`
