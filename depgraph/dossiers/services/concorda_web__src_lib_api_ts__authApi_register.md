---
node_id: concorda-web::src/lib/api.ts::authApi.register
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e53eb6597407392d66a5b30e1486a79e4269ecae2f84c2f30494a8b42dea1411
status: llm_drafted
---

# authApi.register

## Purpose

The `authApi.register` method handles the creation of new user accounts by posting `RegistrationData` to the `/api/auth/register` endpoint. It is a critical entry point for new users and is distinct from `setupAccount`, which is used for completing the onboarding flow after an initial registration step. An agent should use this method when implementing the initial sign-up flow in the registration UI.

## Invariants

- **HTTP Method is POST** — The request must use the `POST` method to the `/api/auth/register` endpoint.
- **Payload is `RegistrationData`** — The body must be a JSON-stringified instance of `RegistrationData`.
- **Return shape is polymorphic** — The response includes `message` and `user_id`, but `transaction_id` and `access_token` are optional depending on the specific registration flow state.

## Gotchas

- **Registration vs. Setup distinction** — Per the structure of `authApi`, `register` creates the identity, while `setupAccount` (using a token and password) is the subsequent step to finalize the account.
- **Dependency on `RegisterPageContent`** — This method is the primary driver for the `RegisterPageContent` component in `src/app/join/register/page.tsx`. Any changes to the `RegistrationData` interface will immediately break this page.

## Cross-cutting concerns

- **Auth**: This is a pre-authentication endpoint; it does not require a bearer token, but its success typically triggers the transition to an authenticated state (e.g., via `setupAccount`).
- **Side effects**: Successful registration is the prerequisite for all subsequent onboarding flows, including `validateSetupToken` and `setupAccount`.

## External consumers

None known.
