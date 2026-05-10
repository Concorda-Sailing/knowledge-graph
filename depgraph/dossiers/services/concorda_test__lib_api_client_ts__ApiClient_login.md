---
node_id: concorda-test::lib/api-client.ts::ApiClient.login
node_kind: service
feature: test-fixtures
last_reviewed: 2026-05-09
last_reviewed_against_hash: 7af3ee8813228f614d83b366f320d49e4e42a00d0aa27c07b478967636853627
status: current
---

# ApiClient.login (concorda-test)

## Purpose

The test-side login helper. Posts to `/api/auth/login`, stores the access token on the `ApiClient` instance, and returns the token string. Every Playwright test that exercises an authenticated flow calls `api.login(USERS.x.email, USERS.x.password)` near the top of the test body to establish credentials before any other API call.

35 tests + setup helpers transitively depend on this method. It is the single de-facto fixture for "authenticate as user X."

## Invariants

- **Mutates `this.token`** — subsequent `this.post`/`this.get`/etc on the same instance will include the bearer header. Tests that need to switch identity within a single test typically `api.setToken(otherToken)` rather than calling login again, but calling login again is also fine and resets the token.
- **Returns the raw token string.** Some tests pass it to `api.setToken(...)` on a *second* `ApiClient` instance to act as a different user from the same test (e.g., owner vs invitee scenarios in `email-link-flows.spec.ts`).
- **`rememberMe = false` by default.** The default 24h token is fine for tests; the 30-day token isn't needed.
- **Follows the production endpoint contract** — `{access_token, token_type}`. If the API endpoint's response shape changes, this method is the first thing that breaks across the test suite.

## Gotchas

- **Tests assume the seeded users in `USERS` (lib/test-data) exist.** They are inserted by `setup/global-setup.ts` via `generateAuthState`. If the global setup is skipped (some test runners' "test single file" mode), login will fail with 401.
- **The test environment skips rate-limiting** (per `_RATE_LIMITS_DISABLED` in the API). Tests can call `api.login()` thousands of times per run. Don't add a sleep/throttle here without thinking through the side effects.
- **Per memory `feedback_no_local_test_runs`** — running this against a local API mutates the local DB (login itself is idempotent but the test as a whole isn't). Always use the test VM or Docker stack.
- **Trust-the-host TLS bypass:** `process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'` at the top of api-client.ts disables cert verification. Necessary because the test host uses self-signed certs. Don't import this client from non-test code.

## Cross-cutting concerns

- **Direct dependent of `POST /api/auth/login`** — see endpoint dossier.
- **Used by every authenticated test pattern.** Two-party flows (owner vs invitee) keep two ApiClient instances, each with its own login.
- **`generateAuthState` in setup uses this** to write storageState files; some Playwright projects (e.g., `dashboard`) use those storageStates to skip per-test login.

## External consumers

- N/A — internal to concorda-test.

## Open questions

- Should `ApiClient.loginAs(userKey: keyof USERS)` exist as a higher-level helper to remove the email/password boilerplate from every test? Would flatten the failure mode when test users are renamed.
