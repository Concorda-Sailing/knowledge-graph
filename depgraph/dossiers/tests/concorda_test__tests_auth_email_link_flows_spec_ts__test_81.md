---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@81
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c6603b489de0904164bb15107f7d3a2b1741f6164c9c3222ffe23a1be318eb11
status: llm_drafted
---

# accept link finalizes the request as approved

## Purpose

Verifies that the email-based invitation flow correctly transitions the state of a crew request. Specifically, it ensures that clicking an "accept" link results in a visible success state, a functional redirect to the dashboard, and a successful status update to `approved` in the API's approval request list. It also validates the "decline" path, ensuring the request status moves to `rejected`.

## Invariants

- **URL structure must contain `requestId`** — The `accept` and `decline` URLs extracted from the email must contain the specific `requestId` to be valid.
- **Session setup is required** — The test must call `setupRecipientSession(page, api, danToken)` to establish the browser context for the recipient before navigating to the decision URL.
- **Status polling is required** — Because the UI-driven action (clicking the link) triggers a backend state change, the test must use `api.poll` to wait for the `listApprovalRequests` status to reach `approved` or `rejected`.
- **Cleanup is mandatory** — To prevent state leakage between tests, the test must manually remove the crew member (using `api.removeCrewMember`) if the test setup created a person in the crew.

## Gotchas

- **Manual cleanup of `danId`** — Per the logic in the test body, if `danCrew` exists, it must be removed via `api.removeCrew-member` to ensure the next test run starts with a clean slate.
- **Race-condition in status updates** — The test relies on `api.poll` with a 5,000ms timeout to observe the status change. If the backend processing of the email link is slow, the `expect(...).toBe('approved')` will fail.

## Cross-cutting concerns

- **Auth**: Uses `danToken` and `bobToken` to simulate different user identities (inviter vs. invitee) within the same test flow.
- **Side effects**: Successfully accepting an invite updates the `status` of a request in `api.listApprovalRequests({ voter: 'me' })`.

## External consumers

None known.
