---
node_id: concorda-test::tests/profile/change-password.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c172540322baa877479d7d863162b67bf63fcb5c88a5435a12c3166444782105
status: current
---

# password change section is accessible

## Purpose

Verifies that the password security section is accessible and functional within the user profile. It ensures that the "Password" tab can be navigated to, that the required input fields (current password, new password, and confirmation) are visible, and that the system correctly handles an incorrect current password by displaying an error message.

## Invariants

- **Tab Navigation**: The test assumes the "Password" tab is reachable via a `getByRole('tab', { name: /password|security/i })` locator.
- **Field Presence**: The "new password" field must be the `.first()` instance of the label to avoid ambiguity in the DOM.
- **Error Visibility**: A successful failure state requires the error message to be visible within a 5,000ms timeout.

## Gotchas

- **Implicit Wait/Race Condition**: The test uses `await page.waitForTimeout(2000)` after clicking the submit button to allow the error message to appear. This is a brittle pattern; if the API response is slow or the network is congested, the `expect(error.first()).toBeVisible()` call may fail.
- **Visibility Guards**: Several blocks (lines 19, 30, 37, 45, 53) use `if (await ...isVisible())` checks. This makes the test non-deterministic; if the UI state changes or the tab fails to load, the test may pass silently without actually asserting the password logic.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established via `ApiClient.login` in a parent `describe` or `beforeEach` block) to access the profile/security tabs.
- **Side effects**: Successful password changes (though not explicitly tested in this specific node) would invalidate existing session tokens or require re-authentication.

## External consumers

None known.
