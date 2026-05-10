---
node_id: concorda-web::src/app/setup-account/page.tsx::SetupAccountPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 82d61ef3cf58f4c3f746d190d884ab4e15dcc4658bd77c6176e85e8d32779046
status: llm_drafted
---

# SetupAccountPage

## Purpose

The entry point for the account setup flow, triggered by a unique setup token in the URL. It manages the lifecycle of a new user's first-time credential creation, transitioning from token validation to password entry. It is distinct from the standard login flow because it must handle specific token states (`used`, `expired`, `invalid`) and pre-populate user data (email, first name) retrieved from the `authApi.validateSetupToken` call.

## Invariants

- **Clears existing session on mount** — Uses `localStorage.removeItem("auth_token")` to ensure a clean state before the user begins the setup.
- **Requires a `token` search parameter** — The component fails to a `invalid` status if the `token` is missing from the URL.
- **Password length minimum is 8 characters** — The `handleSubmit` function enforces this client-side before attempting the API call.
- **Password confirmation is mandatory** — The `password` and `confirmPassword` strings must be strictly equal to pass validation.
- **Uses `authApi.validateSetupToken` for initialization** — This is the single source of truth for the user's email and first name during the setup process.

## Gotchas

- **Autocomplete attributes are required for UX** — Per commit `06075b5`, ensure `name` and `autocomplete` attributes are correctly applied to input fields to support password managers and prevent regressions in user onboarding.
- **Token error handling is string-dependent** — The logic in `useEffect` relies on specific error message substrings (e.g., `"already been used"`, `"expired"`) from the API to set the `tokenStatus`. If the API error messages change, the UI will default to a generic `"invalid"` state.

## Cross-cutting concerns

- **Auth**: Relies on `authApi.validateSetupToken` to establish the identity being set up.
- **Side effects**: Successfully completing this flow results in the creation of a user record and an active session, which is the prerequisite for accessing the dashboard and profile features.

## External consumers

None known.
