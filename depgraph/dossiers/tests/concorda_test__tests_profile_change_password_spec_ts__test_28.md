---
node_id: concorda-test::tests/profile/change-password.spec.ts::test@28
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 256c58ab8c6cf0f041a0cdc47d59a14750abf2f3860cc8b240add7b5e772d141
status: current
---

# password change form has required fields

## Purpose

Verifies the UI state and validation logic for the password change form within the user profile. It ensures that required fields (current, new, and confirm password) are visible and that the system correctly rejects an incorrect current password with a visible error message.

## Invariants

- **Tab visibility check**: The test assumes the "password" tab might be hidden or require a click to reveal the form; it uses `page.getByRole('tab', { name: /password|security/i })` to navigate.
- **Regex-based selection**: Locators for labels and buttons use case-insensitive regex (e.g., `/password|change password|security/i`) to remain resilient to minor text changes in the UI.
- **Error visibility**: A successful "wrong password" flow must result in a visible error message containing terms like "incorrect", "wrong", or "invalid".

## Gotchas

- **Implicit wait for error**: The test uses `await page.waitForTimeout(2000)` to allow the error message to appear after clicking the submit button. This is a brittle way to handle asynchronous UI updates and may lead to flaky results in high-latency environments.
- **Manual tab navigation**: The test relies on checking `if (await passwordTab.isVisible())` before clicking. If the profile structure changes such that the tab is always visible, this logic is redundant but harmless; if the tab is required but not found, the test skips the interaction entirely.

## Cross-cutting concerns

- **Auth**: Requires a valid authenticated session (likely established via `api.login` in a parent `describe` block or `beforeEach` hook) to access the profile settings.
- **Side effects**: Successful password changes (though not explicitly tested in this specific node) would invalidate existing session tokens for the user.

## External consumers

None known.
