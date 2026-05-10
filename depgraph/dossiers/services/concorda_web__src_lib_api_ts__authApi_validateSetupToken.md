---
node_id: concorda-web::src/lib/api.ts::authApi.validateSetupToken
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 75898f6c7ea82e2e72d9e077285155f4848dbbbb7d3524fd3b75c2f1c02584bf
status: llm_drafted
---

# authApi.validateSetupToken

## Purpose

Validates a setup token to verify if a user can proceed with account creation or identity verification. It is a read-only check that returns the user's identity (email and name) associated with the token. This is distinct from `setupAccount`, which is the subsequent POST request that actually binds the password and completes the setup.

## Invariants

- **Method is GET** — The token is passed as a URI-encoded query parameter.
- **Returns identity metadata** — The response shape is strictly `{ valid: boolean; email: string; first_name: string }`.
- **Requires a string token** — The input must be a valid, non-empty string.

## Gotchas

- **Token encoding** — The token must be passed via `encodeURIComponent(token)` to ensure special characters do not break the URI structure, as seen in the implementation of `validateResetToken`.

## Cross-cutting concerns

- **Auth**: Uses a public-facing endpoint; does not require a bearer token, as the token itself is the credential for this specific step.
- **Side effects**: Used by `SetupAccountContent` in `src/app/setup-account/page.tsx` to determine if the user can proceed to the password entry phase.

## External consumers

None known.
