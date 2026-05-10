---
node_id: concorda-test::tests/api/approvals.spec.ts::aliceClient
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4ee129b3233dc915bf0175fd644862347db0d6f7402127b63a66267d64a942ec
status: current
---

# aliceClient

## Purpose

Provides a pre-authenticated `ApiClient` instance for the user "Alice". This is a specialized factory function used to establish an authenticated session for Alice to test boat co-owner promotion flows and approval requests. It is distinct from `bobClient` or `carolClient` which represent different user identities (owners vs. members) required to test multi-party state transitions.

## Invariants

- **Returns a `Promise<ApiClient>`** that is already logged in via `api.login`.
- **Uses `USERS.alice.email` and `USERS.alice.password`** to establish identity.
- **Identity is tied to the `Alice` user record** in the test database.

## Gotchas

- **State leakage between test runs:** Because the test environment may be long-lived, Alice's state (e.g., being a co-owner) can persist across suite runs. Per commit `8644b3d`, tests must explicitly handle the "already a co-owner" state by attempting to remove existing crew members or by wrapping the request in a `try/catch` that calls `test.skip` to avoid false negatives.
- **Sequential dependency:** The `aliceClient` is often used in conjunction with `bobClient` and `carolClient` to simulate a sequence of ownership/approval changes. If Alice's state is not reset, subsequent tests in the same suite may fail with 400 errors if they attempt to re-trigger a promotion that has already occurred.

## Cross-cutting concerns

- **Auth**: Relies on `api.login` using the `USERS.alice` credentials.
- **Side effects**: Changes to the boat ownership/crew state (via Alice's actions) affect the availability of the "co-owner promotion" flow for other users in the same test run.

## External consumers

None known.
