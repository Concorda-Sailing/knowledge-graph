---
node_id: concorda-test::tests/auth/register.spec.ts::test@105
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 36d2dee8f723adfae46cf6fac3cd153ad0ba4a8ead51b9aa107a270fa3fd3d7c
status: llm_drafted
---

# weak password shows validation error

## Purpose

Verifies that the registration UI correctly enforces password complexity requirements. It ensures that a "weak" password (missing uppercase, digits, or sufficient length) prevents the user from proceeding by disabling the `nextButton` and displaying specific validation error text.

## Invariants

- **Validation is real-time.** The `nextButton` must remain in a `disabled` state as long as the password string fails the regex/length requirements.
- **Error visibility is required.** The UI must explicitly render a message containing the text "at least 8 characters" (or similar requirement text) when the password is invalid.
- **Membership selection is a prerequisite.** The test calls `registerPage.selectFreeMembership()` before attempting to trigger the password validation state.

## Gotchas

- **UI Copy Sensitivity.** Per commit `9965eb4`, the registration specs were recently updated to match changes in UI copy/renames; ensure that any changes to the validation error text (e.g., "at least 8 characters") are reflected in the `getByText` locator to avoid brittle failures.
- **Real-time state dependency.** The test relies on the `registerPage` component's internal state management to trigger the `disabled` attribute on the `nextButton` immediately upon the `fill` action.

## Cross-cutting concerns

- **Auth**: Part of the registration flow; success in this test is a prerequisite for the `free signups land on email-verification panel` flow (see commit `98d9ace`).
- **Side effects**: Successful completion of this flow (via subsequent tests) triggers the creation of a new user identity in the test database.

## External consumers

None known.
