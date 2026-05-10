---
node_id: concorda-test::tests/admin/deactivate-reactivate.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5116e73d60dcb1ff78c76a885caf8d0a4809f432f300f1b95c30d894eb0a4206
status: current
---

# admin can deactivate and reactivate a member; login follows

## Purpose

Tests the administrative workflow of deactivating and reactivating a user. It verifies that the UI correctly reflects status changes (Active vs. Inactive) and that the backend enforcement correctly blocks/allows authentication via the `leave_date` gate. This is distinct from general user management tests as it focuses specifically on the side-effect of the `PUT /admin/users/{id}` call on the user's ability to establish a session.

## Invariants

- **UI State Transition**: Deactivating a user must change the status text in the user row from "Active" to "Inactive".
- **Authentication Blocking**: A deactivated user must be unable to successfully call `api.login()` (it must throw an error matching `/account deactivated/i`).
- **Persistence**: Reactivating the user must restore their ability to authenticate and receive a valid token.
- **Admin Authority**: The test requires an authenticated admin session via `USERS.admin` to perform the row-action.

## Gotchas

- **UI Refresh Requirement**: The status change in the UI (e.g., "Inactive" appearing in the row) is not instantaneous upon clicking; the test relies on the table's internal refresh/re-render logic to reflect the backend state change.
- **Dependency on specific UI elements**: The test relies on the row-action dropdown items (`deactivate` / `reactivate`) which were added in `concorda-web 2baa781`.

## Cross-cutting concerns

- **Auth**: Uses `api.login` for both the admin (to perform the action) and the target user (to verify the block).
- **Side effects**: Directly tests the impact of the `leave_date` gate in `routers/auth.py` on the user's authentication flow.

## External consumers

None known.
