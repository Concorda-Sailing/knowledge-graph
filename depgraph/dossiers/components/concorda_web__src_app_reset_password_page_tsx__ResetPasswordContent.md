---
node_id: concorda-web::src/app/reset-password/page.tsx::ResetPasswordContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 06e5b4a3599907609574306992b6ec076860548e1e394d09d2116a06ed3a5341
status: llm_drafted
---

# ResetPasswordContent

## Purpose

The core logic for the password reset flow. It handles the lifecycle of a reset attempt: validating the URL token via `authApi.validateResetToken`, managing the transition between loading/error/success states, and finally executing the password update via `authApi.resetPassword`. It is distinct from the parent `ResetPasswordPage` which only handles the `Suspense` boundary and the `useSearchParams` extraction.

## Invariants

- **Token extraction is mandatory.** The component relies on a `token` query parameter from the URL; if missing, it immediately sets `tokenStatus` to `invalid`.
- **Password length constraint.** The client-side validation requires a minimum of 8 characters before the `authApi.resetPassword` call is even attempted.
- **State-driven UI.** The UI transitions through `loading` -> `valid` (with email populated) -> `complete` (after successful submission).
- **Error handling is granular.** The component catches specific error messages from the API (e.g., "already been used" or "expired") to provide user-friendly feedback rather than generic error strings.

## Gotchas

- **Password Manager Compatibility.** Per commit `06075b5`, this component must include proper `autocomplete` and `name` attributes on input fields to ensure compatibility with modern password managers and browser autofill.
- **Token validation is an effect.** The token validation happens in a `useEffect` triggered by the `token` value. If the `token` is empty or malalformed, the component enters an error state immediately.

## Cross-cutting concerns

- **Auth**: Uses `authApi.validateResetToken` to verify the link and `authApi.resetPassword` to finalize the change.
- **Side effects**: Successful completion of this flow results in a user being able to log in with a new credential, which is a prerequisite for all authenticated flows in the app.

## External consumers

None known.
