---
node_id: concorda-test::tests/boats/coowner-inbox.spec.ts::test@144
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2272d1fb07b185a1720aef11d8ed15d2969f4003c5a32c4abd9c91f9b0fc0192
status: llm_drafted
---

# inviter cancels an outgoing co-owner invite from the Inbox

## Purpose

Verifies that a boat owner (the inviter) can successfully cancel an outgoing co-owner invitation directly from their Inbox UI. This test ensures that the UI state (the "Pending request" alert) and the underlying API state (the request status) stay in sync after a cancellation action. It is distinct from the "accept" flow by specifically targeting the cancellation of an active invitation.

## Invariants

- **Requires two distinct `ApiClient` instances**: One for the inviter (Bob) and one for the invitee (Dan) to simulate independent sessions.
- **Uses `page` for UI interaction**: While the API calls are driven by `bob` and `dan` (the `ApiClient` instances), the visual assertion is performed on the `page` object representing the boat-owner's browser context.
- **Relies on `ensureNotCoowner`**: The test must start with a clean state where the invitee is not already a co-owner, or the `ensureNotCoowner` helper will fail the setup.
- **Status transition is asynchronous**: The test uses a `poll` on the `bob.listApprovalRequests` API endpoint to verify the status reaches `'canceled'` before asserting the UI element is hidden.

## Gotchas

- **Test stack pollution**: The `page.getByRole('alert')` filter is necessary because the test environment may carry pending outgoing invites from previous runs or other tests; the filter ensures we only interact with the alert for the specific `boat.name`.
- **Setup failure sensitivity**: If `ensureNotCoowner` fails, the test uses `test.skip` to avoid false negatives caused by an invalid initial state.

## Cross-cutting concerns

- **Auth**: Uses `bob.login` and `dan.login` to establish two separate authenticated sessions.
- **Side effects**: Affects the `listApprovalRequests` endpoint status and the visibility of the inbox alert component.

## External consumers

None known.
