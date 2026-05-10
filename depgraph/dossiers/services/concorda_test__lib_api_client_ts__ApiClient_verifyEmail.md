---
node_id: concorda-test::lib/api-client.ts::ApiClient.verifyEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 836c0c5c2079e26016c499fe5ab947496f117de1cf10b69a125816a85bf2725b
status: llm_drafted
---

# ApiClient.verifyEmail

## Purpose

The `verifyEmail` method executes a GET request to the `/api/auth/verify-email` endpoint to validate a user's email address via a provided token. It is used in E2E flows to transition a user from a "pending" state to a fully verified state, enabling them to access protected features like boat ownership or crew management.

## Invariants

- **Uses GET method** — The token is passed as a URL query parameter: `?token=${encodeURIComponent(token)}`.
- **Returns `Promise<void>`** — The method does not return a body; success is indicated by a 2xx status code.
- **Requires a single string argument** — The `token` must be the exact string provided by the auth service.

## Gotchas

- **Order of operations in signup flows** — Per commit `eaff02b`, this is a critical step in the "new-crew-signup → publish → crewfinder" chain. If the verification step is skipped or fails, the user remains in a restricted state that prevents them from interacting with the product-specific features (like the "Boats" tab).
- **URL Encoding** — The token must be passed through `encodeURIComponent` to ensure special characters in the token do not break the query string structure.

## Cross-cutting concerns

- **Auth**: Requires a valid session/token if the underlying API endpoint enforces authentication, though typically used for unauthenticated transition flows.
- **Side effects**: Successful verification is a prerequisite for the user to successfully use `getBoats` or `getMyCrewData` in certain lifecycle-dependent E2E tests.

## External consumers

- N/A — internal to concorda-test.
