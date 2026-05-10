---
node_id: concorda-test::lib/api-client.ts::ApiClient.healthCheck
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b70f797b5c8f3f32a143ea9bfa78f42e47c3bef0ca6e7eb7b15a77bea33660b0
status: llm_drafted
---

# ApiClient.healthCheck

## Purpose

Verifies connectivity to the API by polling the `/api/constants` endpoint. It is used by `waitForApi` to block test execution until the backend is ready, ensuring that the test runner doesn't proceed with requests before the server-side environment (or Docker stack) is fully initialized.

## Invariants

- **Returns a boolean.** Returns `true` if the response status is in the 2xx range, and `false` otherwise.
- **Targets the `/api/constants` endpoint.** This is a lightweight endpoint used specifically for connectivity checks.
- **Does not require authentication.** It is a public-facing check to verify the base URL is reachable.

## Gotchas

- **Avoid the "bogus endpoint" trap.** Per commit `c70d472`, do not attempt to use a dedicated `/api/auth/accept-tos` endpoint for setup flows; instead, ensure setup logic delegates to `acceptAllPendingPolicies` to avoid 404 errors that leave users stuck behind policy gates.
- **Reliance on `baseUrl`.** If the `baseUrl` is misconfigured or the remote test host is unreachable, `healthCheck` will return `false` and `waitForApi` will throw an error after the attempt limit is reached.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: N.
- **Rate limit**: none.
- **Side effects**: Used by `waitForApi` to gate the start of the Playwright E2E suite.

## External consumers

None known.
