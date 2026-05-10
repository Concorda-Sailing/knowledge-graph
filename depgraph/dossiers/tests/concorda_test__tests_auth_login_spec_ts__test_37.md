---
node_id: concorda-test::tests/auth/login.spec.ts::test@37
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 74d1821d81b8d460cc4c07ff49aef65183281c92f0922164c3c5ea75f12d73e4
status: current
---

# empty form shows validation

## Purpose

Verifies that the login form's client-side validation triggers correctly when submitted with empty required fields. This test ensures that the browser's native HTML5 validation prevents the form from being submitted to the server when mandatory fields are missing.

## Invariants

- **Submission is blocked by the browser.** The test expects the URL to remain on `/\/login/` after the click, as the form should not submit.
- **Requires `loginPage.signInButton` to be the trigger.** The test relies on the interaction with this specific element to trigger the validation state.

## Gotchas

- **Relies on HTML5 validation behavior.** The test passes by asserting `await expect(loginPage.page).toHaveURL(/\/login/);`, which confirms the page did not navigate away due to a successful submission.

## Cross-cutting concerns

- **Auth**: Tests the boundary of the authentication flow where client-side validation prevents invalid requests from reaching the API.
- **Side effects**: None.

## External consumers

None known.
