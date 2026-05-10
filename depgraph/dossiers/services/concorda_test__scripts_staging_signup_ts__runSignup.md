---
node_id: concorda-test::scripts/staging-signup.ts::runSignup
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 78a92aa25bba6317a7355966fc9c37e35e8f7ac9d3b25e2ec86927a4210765b4
status: llm_drafted
---

# runSignup

## Purpose

The primary orchestration function for the staging signup E2E test suite. It executes a multi-step registration flow—membership selection, info entry, and boat details—to validate that new users can successfully register under specific membership constraints. It is used to verify that the frontend correctly enforces age-based validation and handles email availability checks during the transition between steps.

## Invariants

- **Requires a `slug`** to determine membership type and age-appropriate data (e.g., `young-adult-sailor` vs `boat-owner`).
- **Uses `makeFindings()`** to collect validation results and errors throughout the lifecycle of the test.
- **The `next` button state is a critical checkpoint**; the function throws an error if the button is not enabled after valid data is entered.
- **Email uniqueness is a hard stop**; if the `SIGNUP_EMAIL` is already registered, the function throws an error and terminates the flow.

## Gotchas

- **Age-dependent DOB logic:** The function uses hardcoded logic to select a `dob` based on the `slug` (e.g., `young-adult-sailor` uses 2005 to satisfy a max age of 26). If the membership age constraints change in the application, this script will fail validation.
- **Implicit dependency on `SIGNUP_EMAIL`:** The script relies on a global `SIGNUP_EMAIL` constant. If this email is already in the staging database, the test will fail at Step 4 (the email availability check).

## Cross-cutting concerns

- **Auth**: None (this is a pre-authentication/registration flow).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Creates a new user record in the staging database upon successful completion.

## External consumers

None known.

## Open questions

- Should the `dob` logic be abstracted into a helper that calculates age based on the `slug` to prevent hardcoded date drift?
