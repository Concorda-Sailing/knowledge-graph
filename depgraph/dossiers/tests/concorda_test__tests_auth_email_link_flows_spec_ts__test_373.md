---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@373
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 998ad69db9d72d4d142af75a9543d6e239e40dfd2f58e336904cb792802d5411
status: llm_drafted
---

# crew-request endpoint rejects when accept_crew_requests=false

## Purpose

Verifies the security gate preventing crew requests when an event owner has not opted into receiving them. It ensures that if `accept_crew_requests` is not explicitly set to `true`, the API returns a `403` or a specific error message, preventing unauthorized side effects like database row creation or email dispatch. This test is distinct from the "happy path" tests in the same file because it focuses on the failure mode of the precondition gate.

## Invariants

- **Requires an explicit opt-in.** The test succeeds only if `upsertSailingEvent({accept_crew_requests:true})` is deliberately omitted.
- **Auth identity is critical.** The test uses two distinct identities: `USERS.bob` (the requester/observer) and `USERS.carol` (the owner/target) to verify that the rejection is tied to the owner's settings, not just a lack of permissions.
- **Error shape.** The `api.requestToCrew` call must throw an error containing the string `not accepting crew requests` or a `403` status code.

## Gotchas

- **Order of operations matters.** The test relies on the fact that the API-side rejection happens *before* any side effects (like creating a DB row or sending an email) occur.
- **Cleanup is manual.** Because the test creates a `SailingEvent` and a `Boat` via the API, it must manually call `api.removeScheduleEvent` and `api.removeCrewMember` to prevent state leakage into subsequent tests, as seen in the `api.removeScheduleEvent(event.id).catch(...)` pattern.

## Cross-cutting concerns

- **Auth**: Uses `api.login` for both the requester and the owner to simulate a multi-user interaction.
- **Side effects**: Verifies that the `POST` request does *not* trigger the creation of an `EventCrew` row or any email dispatch when the gate is closed.

## External consumers

None known.
