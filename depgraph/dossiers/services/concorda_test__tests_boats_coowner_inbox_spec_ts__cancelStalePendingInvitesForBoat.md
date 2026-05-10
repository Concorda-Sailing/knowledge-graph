---
node_id: concorda-test::tests/boats/coowner-inbox.spec.ts::cancelStalePendingInvitesForBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 527591ab2d3aa2c51e6963b66b8a3359ce9796a2dc0af453d7efdb58c92a5f02
status: current
---

# cancelStalePendingInvitesForBoat

## Purpose

A cleanup helper used to clear out stale `boat_coowner_invite` requests for a specific boat. It prevents "leaky" state from previous test runs from causing non-strict locator failures in the UI by ensuring the inbox is empty of pending invites before the main test logic begins.

## Invariants

- **Requires an authenticated `ApiClient`** (the `bob` parameter) to perform the cancellation.
- **Filters by `request_type === 'boat_coowner_invite'`** to avoid accidentally canceling other types of approval requests.
- **Uses a type cast for `boat_uuid`** because the standard `ApprovalRequest` type in the `ApiClient` does not natively model the denormalized `boat_uuid` field.
- **Iterates and cancels all matching requests** found in the user's pending list for the given `boatId`.

## Gotchas

- **The test host is long-lived**, meaning prior aborted runs leave a stack of open invites that can cause the Playwright locator to fail due to non-strictness (multiple elements matching).
- **`subject_uuid` is the BoatCrew row ID**, not the Boat ID. The `boat_uuid` must be extracted via a cast to `unknown` as the standard `ApprovalRequest` type lacks this field.

## Cross-cutting concerns

- **Auth**: Uses the provided `bob: ApiClient` instance to call `listApprovalRequests` and `cancelApprovalRequest`.
- **Side effects**: Clears the "Pending request" alerts in the user's Inbox UI, preventing them from interfering with `getByRole('alert')` locators in subsequent test steps.

## External consumers

None known.
