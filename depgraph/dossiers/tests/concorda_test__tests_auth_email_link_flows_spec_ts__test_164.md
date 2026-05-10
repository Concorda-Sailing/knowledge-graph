---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@164
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 126b982e9bae81d43fde9e85b0ee292a42fb855adc242566a8e3fc81bf99b795
status: current
---

# accept link flips EventCrew status to accepted

## Purpose

Verifies the state transitions of an `EventCrew` member when interacting with emailed invitation links. Specifically, it ensures that clicking the "accept" or "decline" link in an email correctly updates the user's status (to `accepted` or `declined` respectively) within the event's crew roster. This test validates the end-to-end flow from email generation via `api.sendEventCrewInvites` to the UI-driven status change.

## Invariants

- **Status transition is permanent until manual intervention.** Clicking the link must result in a status change that is reflected in the `getEventCrew` response.
- **The decision URL is tied to the row ID.** The URL extracted from the email must be the one that resolves through `/api/invite/respond` against the specific `BoatCrew` or `EventCrew` row.
- **Requires a recipient session.** The test must use `setupRecipientSession` to simulate the user's browser context before navigating to the `acceptUrl` or `declineUrl`.

## Gotchas

- **Stale rows break URL extraction.** Per the logic in `inviteCarolToBoatCrew`, if a user is already in the crew, the existing row must be removed via `api.removeCrewMember` before sending the invite. If a stale row persists, the extracted `acceptUrl` will point to an old ID and fail to update the current state.
- **Timeout sensitivity.** The `mail.waitFor` and `expect(...).toBeVisible` calls use a 15,000ms timeout. If the mail capture or the UI rendering of the "Invite accepted/declined" message exceeds this, the test will flake.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(bobToken)` to switch back to the organizer's context to verify the status change after the recipient (Carol) has interacted with the link.
- **Side effects**: Updates the `EventCrew` status, which affects any UI components displaying the event's crew list or participant counts.

## External consumers

None known.
