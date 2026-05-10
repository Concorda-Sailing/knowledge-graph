---
node_id: concorda-web::src/lib/api.ts::authApi.forgotPassword
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5f740fbe998a3f49edeb92d670c8eed88190c833a9b6fb69dd4eac2e6baa160a
status: llm_drafted
---

# authApi.forgotPassword

## Purpose

Triggers the password reset flow by notifying the backend to send a reset email to the provided address. This is a public-facing endpoint used by the `ForgotPasswordPageInner` component. It is distinct from `validateResetToken` and `reset-password`, which are used later in the flow once the user has actually clicked the link in their email.

## Invariants

- **Method is `POST`** — must use `POST` to comply with the API contract.
- **Input is a single string** — the `email` of the user requesting the reset.
- **Returns a success message** — the response shape is `{ message: string }`.
- **Does not require authentication** — unlike `me()` or `logout()`, this is an unauthenticated call used when the user is not logged in.

## Gotchas

- **No rate limiting mentioned in recent history** — while not explicitly documented in the code, the lack of a specific rate-limit error in recent `feat(admin)` or `feat(crew)` commits suggests the backend handles the throttling/security of this endpoint.

## Cross-cutting concerns

- **Auth**: None (this is a pre-auth/unauthenticated endpoint).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Triggers an external email delivery via the backend.

## External consumers

- `concorda-web::src/app/forgot-password/page.tsx` (via `ForgotPasswordPageInner`)
