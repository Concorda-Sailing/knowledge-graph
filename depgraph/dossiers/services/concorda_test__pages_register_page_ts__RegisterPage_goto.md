---
node_id: concorda-test::pages/register.page.ts::RegisterPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 88046a937f944a3830e6e16c3d0125ff10fdf7384774dcac5433ba21672def0e
status: llm_drafted
---

# RegisterPage.goto

## Purpose

Navigates the Playwright browser instance to the registration entry point (`/join/register`). This is the starting point for all new user creation flows in the E2E suite, including both free and paid membership signups.

## Invariants

- **Navigates to `/join/register`** — the hardcoded path for the registration entry point.
- **Requires a fresh browser context** — as this is a registration flow, it assumes no active session exists or that the user is navigating to a public-facing route.
- **Selector-based interaction** — subsequent methods in this class (like `fillPersonalInfo`) rely on the specific DOM structure (IDs like `#dateOfBirth` and `#password`) established during this navigation.

## Gotchas

- **Selector instability** — commit `f552929` fixed a regression where selectors were misaligned with the actual UI; ensure any changes to the registration form are reflected in the `RegisterPage` locators immediately to avoid broken E2E runs.
- **Accessible name requirement** — per commit `030d6f9`, methods like `selectMembershipByName` rely on matching the accessible name (e.g., via `getByRole('radio', { name })`) rather than just text content.
- **Date format dependency** — `fillPersonalInfo` requires a `MM/DD/YYYY` format for the `dateOfBirth` input to satisfy the `isStepValid()` check; failing to provide a valid date string will prevent the registration from advancing.

## Cross-cutting concerns

- **Auth**: None (this is the pre-authentication entry point).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Successful completion of the flows triggered by this page results in a new user record in the database, which impacts subsequent authenticated tests.

## External consumers

None known.
