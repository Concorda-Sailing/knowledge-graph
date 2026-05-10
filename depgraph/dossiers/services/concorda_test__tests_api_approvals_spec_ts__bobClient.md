---
node_id: concorda-test::tests/api/approvals.spec.ts::bobClient
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8fa73b53b03919ee8ddcafd7a5d463905f112902580ec4b75018ac6d6a276a83
status: llm_drafted
---

# bobClient

## Purpose

A factory function that returns an authenticated `ApiClient` instance for the user "Bob". It is used to establish a session for the primary owner of the test boat (`TEST-001`) to perform administrative actions like removing crew members or managing boat ownership.

## Invariants

- **Returns an authenticated `ApiClient` instance.**
- **Uses `USERS.bob.email` and `USERS.bob.password`** for the login call.
- **Requires a valid `ApiClient` constructor** to be available in the scope.

## Gotchas

- **Cumulative-state pollution:** A prior test run may leave a user (like Carol) as a co-owner, which causes subsequent requests to fail with a 400. Per commit `8644b3d`, tests must explicitly reset the state (e.g., by having Bob remove the crew member) before proceeding with a "vote-approve" flow to ensure isolation.
- **Dependency on seeded data:** This client is useless if the test environment hasn't successfully seeded the `USERS.bob` credentials and the associated boat ownership.

## Cross-cutting concerns

- **Auth**: Uses `api.login` with `USERS.bob` credentials.
- **Side effects**: Changes made by this client (like `removeCrewMember`) directly impact the state of the `approvals` API and the ability of other users (like Alice or Carol) to complete the co-owner promotion flow.

## External consumers

None known.
