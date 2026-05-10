---
node_id: concorda-test::lib/api-client.ts::ApiClient.setToken
node_kind: service
feature: e2e-test-infra
last_reviewed: 2026-05-10
last_reviewed_against_hash: 42e99a9e263366f3bc8afacbf73903a36a15a09d377facdd173b357a9562f48c
status: current
---

# ApiClient.setToken

## Purpose

The test-side mechanism for switching identity. Every Playwright spec
that needs to act as a specific persona (Alice the member, Bob the
boat owner, Carol the crew, Eve the event manager, Dan the second
boat owner) calls `client.setToken(<persona's bearer token>)` to
adopt that identity for subsequent API calls.

This is the load-bearing primitive for **persona-driven test design**.
A single `ApiClient` instance is reused across many calls within a
test; the token swap is the only thing that distinguishes "Alice
viewing the schedule" from "Bob viewing the same schedule." 31+ test
files call into this; signature changes propagate widely.

## Invariants

- **Token is in-memory only on this client instance.** No persistence,
  no cookie, no localStorage. Each test's `client` is independent.
- **Setting token to `""` (empty string) is a no-op for headers** (the
  truthy check at `headers()` line 27 falls through; the
  `Authorization` header is omitted). Setting to `null` would also
  work but the type signature requires `string`. Use a fresh client
  instead of "logging out" via empty token in tests that need to
  assert unauthenticated behavior.
- **Trust-self-signed-TLS is set globally** at module load
  (`process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'`). This is fine
  for the test host but means importing this module from non-test
  code would weaken process-wide TLS validation. **Don't import
  this module from production code.**
- **`API_URL` is the test host's API base URL.** Tests run against
  the dev or test VM (per `feedback_no_local_test_runs`), never
  against localhost.

## Gotchas

- **Forgetting to setToken before a call** results in an
  unauthenticated request, which most endpoints reject with 401.
  The error surface in tests is "401 Unauthorized" with no hint that
  the test forgot to switch personas. If you see 401 in a spec
  setup, check the token sequencing first.
- **Token reuse across persona switches** is fine but easy to lose
  track of. Convention: create a single `client` per test and switch
  via `setToken`; or create separate `client` instances per persona
  if interleaved authorization matters within one test.
- **The token itself is ephemeral** (issued by login, expires per
  backend config). For long-running specs, the token can expire
  mid-test. If you see a 401 partway through a previously-working
  spec, the persona token may need refreshing.
- **The `seed_personas.py` fixture** is what mints the tokens used
  by tests. Token strings are not stable across seed runs. Specs
  should always pull tokens from the seed output, never hardcode.

## Cross-cutting concerns

- **E2E test convention** per `feedback_no_local_test_runs`: tests
  run on the test VM, never locally. The DB gets wiped per spec; no
  state survives.
- **Test data** lives at `~/concorda/environment/test/seeds/data/personas.py`
  and is mirrored into `~/concorda-test/lib/test-data.ts`.
- **Mirrored client** in `concorda-web/src/lib/api.ts` (`fetchApi` /
  `fetchApiAuthenticated`) handles the production browser side; this
  `ApiClient` is the test mirror. The two should stay roughly aligned
  in shape but they're separate codebases — the contract is the API
  itself, not the client class.

## External consumers

- All Playwright specs in `concorda-test/tests/`. ~31 hook-call
  edges per depgraph.

## Open questions

- Should there be a helper like `client.asPersona('alice')` that
  pulls the token from a registry by persona name? Cleaner than
  passing token strings around. Cosmetic; not blocking.
- The `'Content-Type': 'application/json'` header is set on every
  request including GETs that don't have a body. Harmless but
  technically wrong; doesn't affect any endpoint behavior.
