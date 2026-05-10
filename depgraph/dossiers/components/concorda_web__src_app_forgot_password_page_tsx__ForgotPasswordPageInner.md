---
node_id: concorda-web::src/app/forgot-password/page.tsx::ForgotPasswordPageInner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 26f224cb6e6eb1d4c4ab9be546dd82df33a80ee118996e5600935601619478dc
status: llm_drafted
---

# ForgotPasswordPageInner

## Purpose

The internal implementation of the Forgot Password page. It handles the user-facing form for requesting a password reset link via email. It is distinct from the main `ForgotPasswordPage` export, which wraps this component in a `Suspense` boundary to handle the `useSearchParams` hook requirements in Next.js App Router.

## Invariants

- **Input is an email string.** The `email` state is initialized from the `email` URL search parameter via `params.get("email")`.
- **Uses `authApi.forgotPassword(email)`.** This is the single source of truth for triggering the reset flow.
- **Success state is non-revealing.** If the email exists, the UI shows a success message; if the API call fails, it displays a generic error to prevent account enumeration/discovery.
- **`isSubmitting` state disables the button.** This prevents multiple concurrent requests to the auth endpoint.

## Gotchas

- **`useSearchParams` requires `Suspense`.** If an agent attempts to move `ForgotPasswordPageInner` to a different layout or remove the `Suspense` wrapper in `ForgotPasswordPage`, the component will throw a runtime error during build/client-side navigation.
- **Email parameter is optional.** The component defaults to an empty string if no `email` param is present, but the `Input` field is marked `required`, ensuring the user must provide an email to submit.

## Cross-cutting concerns

- **Auth**: Calls `authApi.forgotPassword`.
- **Rate limit**: Relies on the backend implementation of the `forgotPassword` endpoint to prevent spamming.
- **Side effects**: Triggers an email dispatch via the auth service.

## External consumers

None known.
