---
node_id: concorda-test::lib/api-client.ts::ApiClient.getProfile
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3436adf2a11510b29ad805cbc2110619778693d9802a390f7dea708b4f1d6231
status: current
---

# ApiClient.getProfile

## Purpose

Fetches the current user's profile data via a `GET` request to `/api/profile`. This is the primary method for verifying the identity and state of the authenticated user within the test suite. It serves as the foundation for tests that need to validate user-specific metadata, such as boat ownership or sailing resumes, before proceeding with more complex flows.

## Invariants

- **HTTP Method is `GET`** — Requests the profile resource without a body.
- **Returns a `Record<string, unknown>`** — The response is a generic object representing the user's profile state.
- **Requires Authentication** — Relies on the `ApiClient` instance having a valid bearer token established via `login`.

## Gotchas

- **Auth Policy Mismatch** — Per commit `c70d472`, the global setup must be configured to accept all pending policies; otherwise, the profile retrieval or subsequent authenticated calls may fail if the user hasn't explicitly accepted terms of service.
- **Dependency on `api-client.ts` structure** — This method is a direct wrapper around `this.get`. If the base `get` implementation or the `/api/profile` endpoint contract changes, this method will fail.

## Cross-cutting concerns

- **Auth**: Requires a valid token from `ApiClient.login`.
- **Side effects**: Used as a baseline to verify state changes in user-centric features like "Boats" or "Sailing Resume" updates.

## External consumers

None known.
