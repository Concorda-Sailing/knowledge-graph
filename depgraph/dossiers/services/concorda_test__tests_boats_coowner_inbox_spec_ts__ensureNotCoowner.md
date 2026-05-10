---
node_id: concorda-test::tests/boats/coowner-inbox.spec.ts::ensureNotCoowner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 968fd15cc220e836a430ad0317be82de6c98b7af9c46a40a4e7106153ab7a582
status: llm_drafted
---

# ensureNotCoowner

## Purpose

A test-side cleanup helper used to ensure a clean state before testing co-owner invitation flows. It removes a specific user (`dan`) from a boat's crew if they are currently listed, preventing existing permissions from interfering with the test's ability to assert that a new invite is required or that the inbox state is predictable.

## Invariants

- **Requires two `ApiClient` instances**: `bob` (the boat owner/initiator) and `dan` (the target user being removed).
- **Requires a valid `boatId`**: The function operates on the crew list of the specific boat provided.
- **Mutates the boat's crew**: If `dan` is found in the crew, `bob.removeCrewMember(boatId, danRow.id)` is called, effectively stripping `dan` of his co-owner status for that boat.

## Gotchas

- **Test host persistence**: Because the test environment is long-lived, prior aborted runs or previous test executions can leave "stale" invites or crew memberships active. If this isn't called, the UI might show a "Pending request" alert from a previous run, causing locators to fail due to non-strictness.
- **Type casting requirement**: Per the source comment, `ApprovalRequest.subject_uuid` is actually the `BoatCrew` row ID, not the `boat_id`. When cleaning up stale invites in the sibling helper `cancelStalePendingInvitesForBoat`, the `boat_uuid` must be accessed via a cast to `unknown` because the `ApiClient` type does not natively model the denormalized `boat_uuid` field.

## Cross-cutting concerns

- **Auth**: Relies on `bob` having sufficient permissions to remove a crew member via `removeCrewMember`.
- **Side effects**: Cleans up state for the "Co-owner Inbox" UI flow, specifically ensuring the "Pending request" alert/inbox entry is not already present when the test begins.

## External consumers

None known.
