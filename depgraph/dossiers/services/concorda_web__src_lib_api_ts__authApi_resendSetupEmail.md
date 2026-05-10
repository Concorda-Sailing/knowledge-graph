---
node_id: concorda-web::src/lib/api.ts::authApi.resendSetupEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 122d4217ba4ca7cda38ebfbcb080b1e9af87786ee400d153b68185aee2bd6486
status: current
---

# authApi.resendSetupEmail

## Purpose

Triggers a request to the backend to resend the initial setup email to a user. This is used during the onboarding flow when a user has not yet completed their account creation via a setup token. It is distinct from `forgotPassword`, which is used for existing users who have already established credentials.

## Invariants

- **Method is `POST`** — requires a POST request to the `/api/auth/resend-setup-email` endpoint.
- **Payload is a JSON object** — the body must contain the `email` string.
- **Returns a success message** — the expected return shape is `{ message: string }`.

## Gotchas

- **Not for existing users** — this is strictly for the setup phase. If a user already has an account, they should use the `forgotPassword` flow instead.
- **Email validation is server-side** — the client does not validate the email format before sending; it relies on the API response to handle invalid or non-existent setup targets.

## Cross-cutting concerns

- **Auth**: none (this is a public endpoint used before a session is established).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: none.

## External consumers

None known.
