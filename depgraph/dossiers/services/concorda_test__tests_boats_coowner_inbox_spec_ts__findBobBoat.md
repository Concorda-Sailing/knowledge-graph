---
node_id: concorda-test::tests/boats/coowner-inbox.spec.ts::findBobBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b77f8c46c062fa38d43bfe9e2cb32173d1567dc45d839801c9524c538014cef8
status: current
---

# findBobBoat

## Purpose

A helper function used to locate the specific boat owned by the user "Bob" (the test-side owner). It retrieves the full boat list via `bob.getBoats()` and filters for the boat matching the name defined in `BOATS.testBreeze.name`. This is used to establish the context for co-owner invitation flows, ensuring the test drives the UI using the correct entity ID.

## Invariants

- **Returns a boat object** containing at least `{ id: string, name: string }`.
- **Requires an active `ApiClient` instance** (specifically `bob`) to perform the `getBoats()` call.
- **Relies on the existence of `BOATS.testBreeze.name`** in the test data to identify the target boat.

## Gotchas

- **Cumulative state dependency:** If a prior test run fails or is aborted, a "stale" invite may still exist. This can cause the UI to show multiple "Pending request" alerts, making Playwright locators non-strict. This is why `cancelStalePendingInvitesForBoat` is called in the `try/catch` block of the main test.
- **Type casting required for `boat_uuid`:** The `ApprovalRequest` type in `ApiClient` does not natively model the `boat_uuid` field. To filter for the correct boat-related invites, the code must cast the request object to `(r as unknown as { boat_uuid?: string })` to access the denormalized boat reference.

## Cross-cutting concerns

- **Auth**: Uses `bob: ApiClient` which must be authenticated via `bob.login()` before calling this function.
- **Side effects**: The results of this function (the `boat.id`) are used to drive the `coownerInvite` endpoint, which creates a pending state in the user's inbox.

## External consumers

None known.
