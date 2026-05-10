---
node_id: concorda-test::tests/auth/login.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 173c122401a4f0188795b0019ba5eabaac1f2d8f3bd49eeaa1152c96cf2a6e9d
status: llm_drafted
---

# wrong password shows error

## Purpose

Verifies that the login form correctly handles invalid credentials and UI-level validation. This test ensures that the `loginPage.errorAlert` is visible when a user provides a wrong password or a non-existent email, and confirms that the UI prevents submission via HTML5 validation for empty fields.

## Invariants

- **Error visibility**: A failed login attempt must result in `loginPage.errorAlert` being visible in the DOM.
- **URL stability**: A successful login must redirect the user to a URL matching the `**/members**` pattern.
- **Form validation**: The `signInButton` click with empty fields must not trigger a navigation, as HTML5 validation prevents the form submission.

## Gotchas

- **HTML5 validation dependency**: The test for empty forms (lines 37-41) relies on the browser's native validation behavior. If the `required` attribute is removed from the input fields, this test will fail as the form will attempt to submit.

## Cross-cutting concerns

- **Auth**: Uses `USERS.alice` from the test data constants to drive negative test cases.
- **Side effects**: None.

## External consumers

None known.
