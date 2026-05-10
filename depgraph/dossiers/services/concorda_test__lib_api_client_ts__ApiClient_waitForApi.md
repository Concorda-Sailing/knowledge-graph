---
node_id: concorda-test::lib/api-client.ts::ApiClient.waitForApi
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9fdc0d9e9ec919c7573829563826b3d66f552d73bdc9b85745332c4221d9cd1d
status: llm_drafted
---

# ApiClient.waitForApi

## Purpose

Provides a polling mechanism to ensure the backend API is responsive before proceeding with test execution. It repeatedly calls `healthCheck()` (which hits `/api/constants`) until the endpoint returns a successful status or the maximum number of attempts is reached. This is used to prevent E2E tests from failing immediately if the test container or local server is still booting up.

## Invariants

- **Relies on `healthCheck()`** — the method's success is strictly tied to the availability of the `/api/constants` endpoint.
- **Default timeout is 30 seconds** — with a default `maxAttempts` of 30 and `delayMs` of 1000.
- **Throws an Error on failure** — if the loop completes without a successful `healthCheck`, it throws a standard `Error` to halt the test runner.

## Gotchas

- **Dependency on `/api/constants`** — if the constants endpoint is renamed or removed, this method will fail even if the rest of the API is functional.
- **Boot-up latency** — if the API takes longer than 30 seconds to initialize (e.g., during heavy database migrations), this will throw and fail the setup phase.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: used in `globalSetup` to ensure the environment is ready before Playwright begins executing tests.

## External consumers

None known.
