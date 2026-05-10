---
node_id: concorda-test::tests/boats/coowner-request.spec.ts::test@36
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3925994b616c4c84fe25f05d3ec4e9a7bb0a7f7566c162883de7c612d504780c
status: current
---

# authenticated user can request co-owner status from profile add-boat

## Purpose

Verifies that a user can initiate a co-owner request via the "Add Boat" flow in the profile section. This test ensures that the UI correctly transitions from a "boat already registered" state to a pending request state, specifically checking for the visibility of the "Request co-owner" button and the subsequent "Pending request" banner on the dashboard.

## Invariants

- **Requires `boat-owner` project auth-state.** The test relies on the Playwright `boat-owner` project to inject `auth-states/boat-owner.json` automatically.
- **Flow sequence:** Navigate to `/members/profile` $\rightarrow$ Click "Add Boat" $\rightarrow$ Fill Sail Number/Name $\rightarrow$ Click "Request co-owner" $\rightarrow$ Click "Add Boat" (confirm) $\rightarrow$ Verify `/members` dashboard banner.
- **UI state dependency:** The "Request co-owner" button only appears after the user attempts to add a boat that is already registered.

## Gotchas

- **Currently skipped.** Per commit `352aac8`, this test is intentionally skipped (`test.skip(true)`) because it requires a seeded existing boat and an updated deployment to pass. Do not enable this test until the staging rollout is complete.
- **Seeding requirement:** To run this test, the environment must have a pre-existing boat record that matches the "USA 12345" / "Sirocco" input to trigger the "already registered" logic.

## Cross-cutting concerns

- **Auth**: Uses `boat-owner` project's `storageState`.
- **Side effects**: Triggers a pending status change in the user's profile/boat relationship, which may affect the user's dashboard view.

## External consumers

None known.

## Open questions

- When is the staging rollout complete so that `test.skip(true)` can be removed?
