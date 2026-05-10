---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@245
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c5cec2c7f46fd53781544533f99d0c788452f423118acb80e9a9389656d216da
status: llm_drafted
---

# accept link flips BoatCrew status to active

## Purpose

Verifies the end-to-end lifecycle of email-based invitations, specifically ensuring that clicking "accept" or "decline" links correctly updates the `BoatCrew` status. It validates that the URL structure contains the correct `crewId` and that the recipient's session transition (via `setupRecipientSession`) correctly lands the user on the dashboard after the decision is made.

## Invariants

- **URL structure must include `crewId`** — The decision URLs (`/members/invite/accept/{crewId}` or `/members/invite/decline/{crewId}`) must contain the specific ID from the `BoatCrew` row to be valid.
- **Status transition is asynchronous** — The test must use `api.poll` to wait for the status change (e.g., to `active` or `declined`) because the state change may not be instantaneous across the API/DB boundary.
- **Cleanup is mandatory** — Tests must call `api.removeCrewMember` at the end of the test to prevent side effects from leaking into subsequent tests in the suite.

## Gotchas

- **Requires `mailCapture.snapshot()`** — The test relies on intercepting the email via `mailCapture` to extract the decision URLs; if the email service or snapshot mechanism fails, the test cannot proceed to the `acceptUrl` or `declineUrl` extraction.
- **Race conditions in status updates** — Per commit `b2f849a`, this test covers the side effects of the link click; if the `poll` timeout (currently 5,000ms) is too short for the backend to process the status flip, the test will fail.
- **Identity switching** — The test requires explicit calls to `api.setToken(bobToken)` and `api.setToken(carolToken)` to simulate the inviter (Bob) checking the status and the recipient (Carol) interacting with the link.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken` to switch between the inviter (Bob) and the recipient (Carol) to verify the status change from both perspectives.
- **Side effects**: Updates the `BoatCrew` status in the database, which affects the visibility of crew members in the boat's roster.

## External consumers

None known.
