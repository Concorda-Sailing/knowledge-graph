---
node_id: concorda-test::tests/api/approvals.spec.ts::carolClient
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ddf44710bf8cf7605b2f8a1f0e0cd32d91dd95fb02261cd3a4c40e8aee5cfcbb
status: current
---

# carolClient

## Purpose

A factory function that returns an authenticated `ApiClient` instance for the user "Carol". It is used to simulate a non-owner (requester) in the boat co-owner promotion flow, distinct from `aliceClient` (used for lookups) or `bobClient` (used for owner/voter actions).

## Invariants

- **Returns a `Promise<ApiClient>`** that is pre-authenticated via `api.login`.
- **Uses `USERS.carol.email` and `USERS.carol.password`** to establish the session.
- **Requires a clean state** for the specific test logic it supports (e.g., ensuring Carol is not already a co-owner before initiating a request).

## Gotchas

- **Cumulative-state dependency:** If a prior test run leaves Carol as a co-owner of a boat, subsequent tests calling `carol.requestCoowner(boatId)` will fail with a 400 error.
- **Manual cleanup required:** Per commit `8644b3d`, the test must explicitly call `bob.removeCrewMember(boatId, carolCrew.id)` to reset the state before the `carolClient` can successfully initiate a new co-owner request.
- **Failure mode:** If the cleanup of the `BoatCrew` row fails, the test is designed to `test.skip` rather than error out to avoid blocking the suite due to stale environment state.

## Cross-cutting concerns

- **Auth**: Authenticates as `USERS.carol`.
- **Side effects**: The `requestCoowner` call initiated by this client creates an approval request record that must be managed/cleared to prevent state leakage between test runs.

## External consumers

None known.
