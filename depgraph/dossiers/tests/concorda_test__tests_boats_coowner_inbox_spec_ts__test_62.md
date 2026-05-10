---
node_id: concorda-test::tests/boats/coowner-inbox.spec.ts::test@62
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dc3a9cd9b1c9b3113f40fc7e075bf54f4a1354dd588c93c46c5e97b1d0586a14
status: current
---

# receiver accepts an incoming co-owner invite from the Inbox

## Purpose

Verifies the end-to-end flow of a co-owner invitation being received and accepted via the web UI. It ensures that when a user (Bob) invites another user (Dan) to a boat, the invitation appears as an "Action needed" alert in the recipient's (Dan's) Inbox, and that clicking "Accept" both clears the UI alert and updates the server-side request status to `approved`.

## Invariants

- **Two-persona flow**: Requires two distinct `ApiClient` instances (Bob and Dan) and a Playwright `persona` (Dan) to simulate the transition from API-driven setup to UI-driven interaction.
- **Inbox filtering**: The UI alert must be filtered by both the text `"Action needed"` and the specific `boat.name` to avoid collisions with other pending alerts.
- **State verification**: The test must verify both the UI state (alert is hidden) and the API state (request status is `approved`) to ensure the frontend and backend are in sync.
- **Cleanup dependency**: Relies on `cancelStalePendingInvitesForBoat` and `ensureNotCoowner` to reset the environment, ensuring the test doesn't fail due to leftover state from previous runs.

## Gotchas

- **Stale state sensitivity**: Per commit `03a3cdd`, this test is sensitive to stale pending alerts. If `cancelStalePendingInvitesForBoat` or `ensureNotCoowner` fails, the test skips rather than failing, as a cluttered inbox can cause locators to fail or pick the wrong row.
- **Timeout requirements**: The `inboxLink` and the `alert` both require an explicit `10_000`ms timeout because the transition from the `/members` page to the `/members/inbox` route and the subsequent rendering of the alert can be slow in the test environment.

## Cross-cutting concerns

- **Auth**: Uses `bob.login` and `dan.login` to establish identity for both the API-side setup and the Playwright-side UI interaction.
- **Side effects**: Successful acceptance updates the `status` of the `ApprovalRequest` in the database, which is verified via `dan.listApprovalRequests`.

## External consumers

None known.
