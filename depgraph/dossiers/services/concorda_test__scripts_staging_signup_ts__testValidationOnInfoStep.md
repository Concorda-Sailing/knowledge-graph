---
node_id: concorda-test::scripts/staging-signup.ts::testValidationOnInfoStep
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ddafeb63ba364e48ab78bd981b8116a96ed0f8d5f0bae64df84faf4434029391
status: current
---

# testValidationOnInfoStep

## Purpose

Validates the client-side form validation logic for the "Information" step of the staging signup flow. It specifically tests that error messages and button states (like the `next` button's disabled state) respond correctly to invalid inputs for email, password, and date of birth. This is a diagnostic helper used to ensure the UI prevents users from proceeding with malformed data before any API calls are made.

## Invariants

- **Input is simulated via Playwright keyboard/fill actions.** The function relies on direct interaction with `#email`, `#confirmEmail`, `#password`, `#confirmPassword`, and `#dateOfBirth` locators.
- **Results are pushed to `findings.validationTests`.** Every test case must append a result object with `scenario`, `passed`, and `detail` keys to the provided `Findings` instance.
- **Uses `page.waitForTimeout(200)` for debounce/rendering.** The function assumes a small delay is necessary for the UI to react to input changes and display error messages.

## Gotchas

- **Manual typing required for email confirmation.** Per the logic in the `fillInfoStep` (implied by the `await page.keyboard.type(data.email)` pattern at line 109), the `#confirmEmail` field blocks standard `fill()` operations to prevent paste-based errors; `testValidationOnInfoStep` follows this by using `page.keyboard.type` for the mismatch test to ensure the error triggers correctly.
- **Regex-based error detection.** The function uses `page.getByText(/.../i)` to find error messages. If the UI text changes (e.g., "please enter a valid email" becomes "invalid email format"), the test will fail even if the validation logic is working.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Validates the UI state before `runSignup` is called.

## External consumers

None known.
