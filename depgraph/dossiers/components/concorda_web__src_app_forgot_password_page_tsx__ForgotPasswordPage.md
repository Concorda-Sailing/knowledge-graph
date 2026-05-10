---
node_id: concorda-web::src/app/forgot-password/page.tsx::ForgotPasswordPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1a4eb50a449d97f61cd886136e8384ab4568ff9827856eb5776e1a7dbc6f4a41
status: llm_drafted
---

# ForgotPasswordPage

## Purpose

The entry point for the password reset request flow. It provides a UI for users to submit an email address to trigger a reset link via the `authApi.forgotPassword` method. It is distinct from the actual reset-password form (which requires a token) by being the unauthenticated trigger that initiates the process.

## Invariants

- **Uses `useSearchParams` for pre-filling.** The `email` state is initialized from the `email` query parameter to allow for seamless transitions or deep-linking if needed.
- **Submits via `authApi.forgotPassword`.** The component relies on this specific method to communicate with the backend.
- **State-driven UI transitions.** The view switches between the input form and a success message (`isSubmitted`) based on the success of the API call.
- **Error handling is local.** Errors caught during submission are stored in the `error` state and displayed within the card to the user.

## Gotchas

- **Security/Privacy UX.** Per the UI text in the success state, the component explicitly states: "If an account exists with that email, we've sent a password reset link." This is a deliberate design choice to prevent user enumeration/account discovery via the UI.
- **Public access.** This page is part of the public-facing auth flow (per commit `fd7fd0f`) and does not require an active session to render or submit.

## Cross-cutting concerns

- **Auth**: Uses `authApi.forgotPassword`.
- **Audit**: N/A.
- **Rate limit**: Dependent on the rate-limiting policies applied to the `forgotPassword` endpoint in `authApi`.

## External consumers

None known.
