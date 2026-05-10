---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@402
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2d4a58232245bb1ae17faae3f17b803e1e656c8761381b54332352e283218788
status: llm_drafted
---

# accept link flips EventCrew status to accepted and promotes to BoatCrew

## Purpose

Verifies the state transitions of a user's relationship to an event and a boat via email-driven decision links. Specifically, it ensures that "accepting" an invite via a URL updates both the `EventCrew` status to `accepted` and promotes the user to `BoatCrew` (role='crew', status='active'), while "declining" updates the `EventCrew` status to `declined` without touching the `BoatCrew` membership.

## Invariants

- **Acceptance triggers dual updates**: Successful acceptance must update `EventCrew.status` to `'accepted'` AND perform an upsert on `BoatCrew` with `role='crew'` and `status='active'`.
- **Decline is localized**: Declining an invite must change `EventCrew.status` to `'declined'` but must not create or modify any records in the `BoatCrew` table.
- **URL structure**: The decision URL must contain the specific pattern `/members/invite/accept/${eventCrewId}` or `/members/invite/decline/${eventCrewId}`.
- **Reply-To integrity**: The email `reply_to` field must be set to the requester's email (e.g., `USERS.carol.email`) to allow plain-text replies to route correctly.

## Gotchas

- **State cleanup is mandatory**: Because these tests mutate the database (creating `BoatCrew` rows), the test must manually call `api.removeCrewMember` and `api.removeScheduleEvent` in a `catch` block to ensure the next test starts with a clean baseline. Failure to do so causes subsequent tests to fail due to unexpected existing records.
- **Race conditions in setup**: The test relies on `carolRequestsToCrew` to establish the initial state; if the helper doesn't properly clean up or if the sequence of events is interrupted, the `baseline` check (verifying the user is NOT on `BoatCrew`) will fail.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(bobToken)` to simulate the recipient's identity and `setupRecipientSession` to handle the browser-side session.
- **Side effects**: Updates `EventCrew` status and potentially creates/modifies `BoatCrew` membership.
- **Logic Mirroring**: The behavior of the email links is a direct mirror of the `routers/events.py` `respond_to_crew_request` logic.

## External consumers

None known.
