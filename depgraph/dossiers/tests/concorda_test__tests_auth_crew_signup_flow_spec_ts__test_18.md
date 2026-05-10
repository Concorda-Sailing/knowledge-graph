---
node_id: concorda-test::tests/auth/crew-signup-flow.spec.ts::test@18
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b55cfc56b4903c4dfd66fbcdd8b8944e7ad2ee6d7244f8ad02b11ed6d29a935c
status: llm_drafted
---

# new free member can fill resume and appear in crewfinder

## Purpose

This E2E test validates the full lifecycle of a new free member: from registration and email verification to completing the sailing-resume wizard and appearing in the Crew Finder. It combines API-driven setup (registration, verification, and preference seeding) with UI-driven interaction (the setup wizard and publish-bar) to ensure the handoff between the backend and the frontend components is seamless.

## Invariants

- **Registration must echo the `verification_token`** — the API must return the token in the response body for the test to proceed to the verification step.
- **The setup wizard is UI-driven** — while profile data can be seeded via API, the test specifically uses `SetupWizardPage` to validate the UI-based completion flow.
- **The `auth_token` must be manually injected** — the test relies on `page.evaluate` to set the token in `localStorage` to simulate a signed-in state before navigating to the wizard.
- **The `publish-bar` requires specific data** — the test must seed `race_areas` and `availability` via the API to ensure the completeness check passes and the user is visible in Crew Finder.

## Gotchas

- **UI vs. API split** — the wizard's auto-save behavior is a critical timing factor; the test uses `waitForAutoSave` to block on the `PUT /profile/sailing-resume` response to prevent race conditions.
- **Specific string literals** — per commit `eaeee2c`, the test must use the exact position name `"Main Trim"` rather than `"Trimmer"` to ensure the UI-driven part of the wizard accepts the input.
- **Identity visibility** — as noted in commit `c200d4d`, this test validates that a new member is visible to others (e.g., a boat owner) in the `/members/crewfinder` view.

## Cross-cutting concerns

- **Auth**: Uses `api.register`, `api.verifyEmail`, and `api.login` to establish identity; requires `localStorage` injection for the UI-driven steps.
- **Side effects**: Successful completion of this test makes the user visible in the `/members/crewfinder` view.

## External consumers

None known.
