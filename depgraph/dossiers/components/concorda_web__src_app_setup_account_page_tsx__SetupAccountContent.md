---
node_id: concorda-web::src/app/setup-account/page.tsx::SetupAccountContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6575fac495c93109afdc0994fce972526bc051adc940f0ef31c3901a413290ca
status: current
---

# SetupAccountContent

## Purpose

The core UI logic for the account setup flow. It handles the lifecycle of a single-use setup token, from validation via `authApi.validateSetupToken` to the finalization of the account via `authApi.setupAccount`. It is distinct from the standard login flow because it is a transient, unauthenticated state used to transition a user from a "pending" status to a fully registered account.

## Invariants

- **Token-driven state**: The component's lifecycle is strictly bound to the `token` query parameter.
- **Mandatory token validation**: The component must call `authApi.validateSetupToken` before allowing a password submission to prevent unauthorized account creation.
- **Password constraints**: A successful submission requires a password of at least 8 characters and a match with `confirmPassword`.
- **Post-completion redirect**: Upon successful `setupAccount` call, the user is redirected to `/login` after a 2-second delay.

## Gotchas

- **Session clearing**: The component explicitly calls `localStorage.removeItem("auth_token")` on mount to ensure a clean state and prevent existing sessions from interfering with the setup flow.
- **Error-driven state transitions**: The `tokenStatus` is updated based on specific error message strings (e.g., `"already been used"` or `"expired"`) returned by the API. If the API error messages change, the UI will fail to show the correct reason for the failure.
- **Commit `06075b5`**: Recent changes added proper `autocomplete` and `name` attributes to ensure compatibility with password managers during the setup process.

## Cross-cutting concerns

- **Auth**: Uses `authApi.validateSetupToken` and `authApi.setupAccount` to transition a user from a token-based state to an authenticated state.
- **Side effects**: Successful completion triggers a redirect to the `/login` page.

## External consumers

None known.
