---
node_id: concorda-web::src/app/reset-password/page.tsx::ResetPasswordPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 079fb5ba203827af841dc1dcdf41adee24be843edcfdd7b5c8b094844ae51ce0
status: current
---

# ResetPasswordPage

## Purpose

The entry point for the password reset flow. It extracts the `token` from the URL search parameters and uses `authApi.validateResetToken` to determine the current state of the reset attempt (valid, expired, or used) before allowing the user to submit a new password. It serves as the orchestration layer for the `ResetPasswordContent` component.

## Invariants

- **Requires a `token` query parameter.** The page will transition to an `invalid` state immediately if no token is present in the URL.
- **Token validation is the first step.** The component must successfully call `authApi.validateResetToken` and receive a valid response before the user can interact with the password input fields.
- **Password length constraint.** The client-side validation requires a minimum of 8 characters before the `authApi.resetPassword` call is attempted.
- **Strict password matching.** The `handleSubmit` function enforces that `password === confirmPassword` before proceeding to the API call.

## Gotchas

- **Commit `06075b5` (chore(auth-forms))** addressed issues with password managers. Ensure that any changes to the input fields maintain proper `name` attributes and `autocomplete` attributes to prevent breaking compatibility with browser-based credential managers.
- **Error message parsing is brittle.** The `useEffect` hook relies on string matching (e.g., `msg.includes("already been used")`) to differentiate between an expired token and a used token. If the API error messages change, the UI will incorrectly report the wrong status to the user.

## Cross-cutting concerns

- **Auth**: Uses `authApi.validateResetToken` and `authApi.resetPassword` to interact with the authentication backend.
- **Side effects**: Successful completion of this flow changes the user's credentials, which will invalidate any existing sessions/tokens for that user.

## External consumers

None known.
