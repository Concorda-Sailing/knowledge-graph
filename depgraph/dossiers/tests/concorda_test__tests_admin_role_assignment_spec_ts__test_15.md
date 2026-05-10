---
node_id: concorda-test::tests/admin/role-assignment.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fdbca24a91c8d2a4580449a57a60f481b0906acad638c8f30b1e05f3a54e82ed
status: current
---

# admin grants and revokes event_manager role on a member

## Purpose

Verifies the end-to-end lifecycle of granting and revoking the `event_manager` role via the Admin UI. It ensures that role changes made in the `UserDialog` correctly propagate to the permission gate in `AdminLayout`, allowing or restricting access to sensitive routes like `/members/admin/events`.

## Invariants

- **Role lifecycle is idempotent.** The test must ensure the user starts without the role; if the role is present, it must be revoked before the test proceeds to ensure a clean baseline.
- **Identity switching requires manual state management.** The test uses `page.evaluate` to set the `auth_token` in `localStorage` and `context.clearCookies()` to simulate switching between the Admin and the subject user (Alice).
- **UI Selectors are specific.** The role checkbox is identified by the ID pattern `role-<name>` (e.g., `#role-event_manager`).

## Gotchas

- **Search is required due to seed volume.** Because the production seed contains 635 rows, the test must use the search input to narrow the table to "alice" before the row becomes reliably locatable. (See commit `dad4d2e`).
- **Tests are not naturally idempotent.** If a previous run fails or leaves the user with the role, the test will fail the assertion that the checkbox is unchecked. The logic to "revoke if checked" was added to prevent this state leakage. (See commit `84a30be`).
- **Race conditions on navigation.** The test relies on `page.waitForLoadState('networkidle')` after searching to ensure the table has populated before attempting to click the row actions.

## Cross-cutting concerns

- **Auth**: Uses `ApiClient.login` to establish the `adminToken` and `aliceToken`.
- **Side effects**: Mutates the user's role in the database, which affects the visibility of the `Access Denied` card in `AdminLayout` (via `contexts/auth-context.tsx`).

## External consumers

None known.
