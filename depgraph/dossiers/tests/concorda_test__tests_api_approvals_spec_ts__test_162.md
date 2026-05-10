---
node_id: concorda-test::tests/api/approvals.spec.ts::test@162
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 20e6a48dc6503b5db90b1aa54f1985f4ff1938f4e5843786ce1d60d63981a5fb
status: llm_drafted
---

# unauthenticated GET returns 401

## Purpose

Verifies the security boundaries of the Approvals API, specifically ensuring that unauthenticated or unauthorized users cannot access or manipulate approval requests. This test ensures that the system correctly enforces ownership and permission constraints (e.g., preventing a non-voter from voting on a request).

## Invariants

- **GET `/api/approval-requests` without filters returns 400.** The API requires specific query parameters to prevent broad data exposure.
- **Unauthenticated requests return 401 or 403.** The `ApiClient` must be instantiated and authenticated to access the `voter=me` endpoint.
- **Unauthorized voting attempts are blocked.** A user without ownership of the associated `boatId` must not be able to successfully POST to the `/vote` endpoint.

## Gotchas

- **State dependency on prior runs:** The test `non-voter cannot vote on an unrelated request` uses a `try/catch` block around `carol.requestCoowner(boatId)` because the user might already be a co-owner from a previous test run, which would cause the setup to fail.
- **Reset requirement:** Per commit `8644b3d`, the co-owner state must be explicitly reset before the vote-approve flow to ensure test isolation and prevent false positives in the negative path testing.

## Cross-cutting concerns

- **Auth**: Requires `aliceClient()` or `carolClient()` to establish identity; `api.rawRequest` with no token results in 401/403.
- **Side effects**: Successful or failed votes may impact the state of the `approval-requests` lifecycle, though this test focuses on the failure modes.

## External consumers

None known.
