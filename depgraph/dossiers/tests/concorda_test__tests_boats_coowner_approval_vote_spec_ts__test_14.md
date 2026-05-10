---
node_id: concorda-test::tests/boats/coowner-approval-vote.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c1e3167d62ce46c675c2c17a21916431a16fcdf0488dc80d4c1f1c77b071dbd4
status: current
---

# owner sees pending approval and can accept it

## Purpose

Tests the UI-driven lifecycle of a co-owner request from the perspective of the boat owner. It verifies that a pending request appears in the "Pending approvals" panel on the boat detail page and that the owner can either accept or reject the request, with the state change reflecting correctly in both the UI and the backend API.

## Invariants

- **Requires dual-session setup**: The test must instantiate two separate `ApiClient` instances (e.g., `carolApi` and `bobApi`) to simulate the requester and the owner.
- **Server-side setup is mandatory**: The request must be initiated via the API (e.g., `carolApi.requestCoowner`) before the Playwright `page` navigates to the boat detail view to ensure the "Pending approvals" panel is populated.
- **State verification is asynchronous**: Verification of the `status` (e.g., `'approved'` or `'rejected'`) must use `expect.poll` to account for the delay between the UI action and the API state update.

## Gotchas

- **Idempotency/State leakage**: If a test run fails or is interrupted, the user might already be a co-owner, causing `requestCoowner` to throw. The test handles this via a `try/catch` block that calls `test.skip(true, ...)` to prevent subsequent runs from failing due to existing state.
- **Trace artifacts**: Per commit `0990b5d`, this test uses `test.use({ trace: 'on' })`, meaning it generates heavy trace and screenshot artifacts which are useful for debugging the "Pending approvals" panel visibility.

## Cross-cutting concerns

- **Auth**: Uses `ApiClient.login` for both the requester and the owner to establish distinct sessions.
- **Side effects**: Successful acceptance/rejection updates the boat's membership state and the `listApprovalRequests` response for the requester.

## External consumers

None known.
