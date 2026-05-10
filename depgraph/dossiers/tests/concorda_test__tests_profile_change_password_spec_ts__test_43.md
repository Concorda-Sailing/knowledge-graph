---
node_id: concorda-test::tests/profile/change-password.spec.ts::test@43
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c4caf75fa62f4fd968d0363fdcfe182fb09633d79ff2a2ea4d5336c5be7d9028
status: current
---

# wrong current password shows error

## Purpose

Verifies that the password change flow correctly rejects an incorrect current password. It ensures the UI displays a visible error message when a user attempts to update their credentials with a mismatch. This test is distinct from the successful change-password flow, as it specifically targets the error-handling state of the security tab.

## Invariants

- **Requires visibility of the password tab** — The test checks for the presence of the `password|security` tab before attempting to interact with it.
- **Requires visibility of the current password field** — The test only proceeds with the assertion if `currentPassword` is visible, preventing false negatives in non-standard UI states.
- **Expects an error message** — The test asserts that an element matching the regex `/incorrect|wrong|invalid|error/i` becomes visible.
- **Uses a hard-coded timeout** — The test relies on a 2000ms `page.waitForTimeout` to allow the error to propagate before checking visibility.

## Gotchas

- **Brittle visibility checks** — The test uses `if (await currentPassword.isVisible())` as a guard. If the UI structure changes such that the field is present but not "visible" (e.g., due to a loading state or different CSS), the test will silently skip the assertion rather than failing.
- **Implicit dependency on tab state** — The test assumes the user is either already on the security tab or can navigate to it via `page.getByRole('tab', { name: /password|security/i })`.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (established in the `beforeEach` or parent test block) to access the profile/security settings.
- **Side effects**: None.

## External consumers

None known.
