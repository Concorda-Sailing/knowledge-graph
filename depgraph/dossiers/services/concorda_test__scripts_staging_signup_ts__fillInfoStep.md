---
node_id: concorda-test::scripts/staging-signup.ts::fillInfoStep
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7f933d92762015aef5df35d74a47b8ffd82f01fdc58945168dd88b6a9927108a
status: llm_drafted
---

# fillInfoStep

## Purpose

The `fillInfoStep` function automates the population of the user information form during the staging signup flow. It is used to transition the Playwright test from the initial identity creation to the secondary metadata entry phase. Use this helper when a test needs to complete the user profile creation (name, email, phone, DOB, and password) to reach the authenticated state.

## Invariants

- **Requires a `Page` instance and a specific `data` object** containing `firstName`, `lastName`, `email`, `phone`, `dateOfBirth`, and `password`.
- **Uses `keyboard.type` for the email confirmation field.** This is necessary because the `#confirmEmail` input field blocks standard `.fill()` or paste operations.
- **Populates both `#password` and `#confirmPassword` with the same value.** The function assumes the provided `data.password` is the intended final password.

## Gotchas

- **The email confirmation field blocks paste.** As noted in the source comment (line 107), `await page.locator('#confirmEmail').click()` must be followed by `await page.keyboard.type(data.email)` rather than using `.fill()` to ensure the input is accepted by the UI.
- **The function is part of the initial scaffolding.** Per commit `fd0c570`, this is part of the new Playwright E2E suite scaffolding; ensure that any changes to the signup form selectors are reflected here to avoid breaking the entire staging setup flow.

## Cross-cutting concerns

- **Auth**: Directly facilitates the creation of user credentials required for subsequent authenticated sessions.
- **Side effects**: Success in this step is a prerequisite for the `testValidationOnInfoStep` logic to proceed to authenticated dashboard states.

## External consumers

None known.
