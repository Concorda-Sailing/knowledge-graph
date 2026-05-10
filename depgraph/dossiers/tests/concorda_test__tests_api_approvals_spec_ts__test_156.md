---
node_id: concorda-test::tests/api/approvals.spec.ts::test@156
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f53ef92f1ea596ab82c327363ac34c610af6a6b045f08afa4f3053867fe2f3d7
status: llm_drafted
---

# GET without a filter returns 400

## Purpose

Verifies negative authorization and validation paths for the Approvals API. Specifically, it ensures that the system correctly rejects requests when required filters are missing, when the user is unauthenticated, or when a non-owner/non-voter attempts to vote on a request. This prevents unauthorized users from manipulating boat ownership or approval states.

## Invariants

- **GET `/api/approval-requests` without filters returns 400.** The API requires specific query parameters to prevent broad data exposure.
- **Unauthenticated requests return 401 or 403.** The `ApiClient` without a token must fail to access the endpoint.
- **Non-voters are blocked from voting.** A user without ownership or specific voter rights must receive a 400, 403, or 404 when attempting a `POST` to the vote endpoint.

## Gotchas

- **State dependency on `requestCoowner`.** The test relies on `carol.requestCoowner(boatId)` to set up the initial state. Per commit `8644b3d`, the test must ensure the co-owner state is correctly reset or handled to avoid failure if a previous run left the user as an owner.
- **Error handling in setup.** If `requestCoowner` fails, the test uses `test.skip(true, ...)` to exit gracefully rather than failing the suite, as the user might already be a co-owner from a prior run.

## Cross-cutting concerns

- **Auth**: Uses `aliceClient()` and `carolClient()` to simulate different permission levels (unauthenticated vs. unauthorized vs. authorized).
- **Side effects**: The test performs a cleanup via `carol.cancelApprovalRequest(request_id)` to ensure the created approval request does not persist and affect subsequent test runs.

## External consumers

None known.
