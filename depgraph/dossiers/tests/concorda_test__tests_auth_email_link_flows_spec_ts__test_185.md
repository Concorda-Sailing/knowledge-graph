---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@185
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2bafebae4e04fcd3e849b88718fe65ecf50d51adcd8b6234d6aea2b3b42a57c2
status: current
---

# decline link flips EventCrew status to declined

## Purpose

Verifies that clicking a "decline" link in an invitation email correctly updates the recipient's status in the `EventCrew` table. This test ensures that the decision URL extracted from the email correctly targets the `/api/invite/respond` endpoint (or equivalent) to transition a user from an invited state to a `declined` state, preventing stale or unhandled invite statuses in the event lifecycle.

## Invariants

- **Status Transition**: The `person_uuid` in the `EventCrew` row must transition to `declined` after the user navigates to the decision URL.
- **URL Integrity**: The `declineUrl` must be hosted on the test environment and contain the correct decision token.
- **Identity Context**: The test requires two distinct identities: the inviter (Bob) to verify the resulting state, and the recipient (Carol) to perform the action.

## Gotchas

- **Idempotence Requirement**: Per the `inviteCarolToBoatCrew` helper, any existing `BoatCrew` row for the recipient must be removed before the test runs. If a stale row exists, the email URL might point to an old ID, causing the test to fail or verify the wrong record.
- **Email Timing**: The test relies on `mailCapture.snapshot()` and `mail.waitFor`. If the email delivery is delayed beyond 15,000ms, the `extractDecisionUrl` step will fail.
- **Identity Switching**: The test must explicitly call `api.setToken(bobToken)` after the user-side action to verify the backend state change, as the `ApiClient` instance used for the action is distinct from the one used for verification.

## Cross-cutting concerns

- **Auth**: Uses `api.login` to establish sessions for both the inviter and the recipient.
- **Side effects**: Updates the `EventCrew` status in the database; failure to clean up via `api.removeScheduleEvent` can leave orphaned rows that break subsequent test runs.

## External consumers

None known.
