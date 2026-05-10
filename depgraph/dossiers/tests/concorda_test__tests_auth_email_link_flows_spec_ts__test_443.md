---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@443
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85deb7d808a1f6b33c8ee4d8ded2d81a2c00ae118f38440f6c101f868e063aff
status: current
---

# decline link flips EventCrew status to declined and does not touch BoatCrew

## Purpose

Verifies that clicking a "decline" link in a crew invitation email correctly updates the `EventCrew` status to `declined` without affecting the `BoatCrew` membership. This test ensures that a rejection is localized to the specific event and does not inadvertently add the user to the boat's permanent crew list. It is a critical check for the isolation between event-level participation and boat-level membership.

## Invariants

- **`EventCrew` status change**: The `status` field for the specific `eventCrewId` must transition to `'declined'`.
- **`BoatCrew` isolation**: The user (Carol) must not be present in the `getBoatCrew` response after the decline action is completed.
- **URL structure**: The decline link must be hosted on the test environment and contain the specific path `/members/invite/decline/${eventCrewId}`.
- **Session requirement**: The recipient must have a valid session (via `setupRecipientSession`) to interact with the hosted decline URL.

## Gotchas

- **Precondition cleanup**: The test relies on `carolBoatRow` being removed via `api.removeCrewMember` and `api.removeScheduleEvent` before the test starts to ensure the baseline is truly empty. If the cleanup fails or is skipped, the `expect(...).toBeUndefined()` check on line 454 will fail.
- **Email subject regex**: The mail capture looks for a subject matching `/Crew request:/i`. If the email template text changes, this test will time out waiting for the message.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(bobToken)` to establish the identity of the person interacting with the link.
- **Side effects**: Verifies that the `EventCrew` record is updated, but ensures no side effects occur on the `BoatCrew` collection.

## External consumers

None known.
