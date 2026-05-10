---
node_id: concorda-test::tests/auth/login.spec.ts::test@32
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d339243ec7ebb980ad5d4b25cfa6310b679b7c89386c5f3f487e88d5ccfdffe5
status: current
---

# non-existent email shows error

## Purpose

Verifies that the login UI correctly handles invalid credentials and non-existent users. It ensures that the `errorAlert` is visible when the backend rejects the authentication attempt, preventing users from being redirected to the dashboard on failure.

## Invariants

- **Error visibility**: On failed login (wrong password or non-existent email), `loginPage.errorAlert` must be visible.
- **URL stability**: Successful login (implied by the preceding test in the file) redirects to `/members`, while failed attempts must keep the user on the `/login` route.
- **Form validation**: Empty field submission is caught by HTML5 validation, preventing the form from submitting and ensuring the URL remains `/login`.

## Gotchas

- **HTML5 Validation**: The test for empty forms relies on the browser's native `required` attribute behavior. If the `signInButton.click()` is used to test submission, the test must account for the fact that the URL will not change because the browser prevents the request.

## Cross-cutting concerns

- **Auth**: Directly tests the failure paths of the authentication flow.
- **Rate limit**: None.

## External consumers

None known.
