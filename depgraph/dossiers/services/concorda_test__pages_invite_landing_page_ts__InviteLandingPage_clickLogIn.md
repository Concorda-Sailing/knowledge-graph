---
node_id: concorda-test::pages/invite-landing.page.ts::InviteLandingPage.clickLogIn
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6cd00b6b328775ae7655b2d89704df6187e6a47925cdd269a9193fe3f574ba1c
status: current
---

# InviteLandingPage.clickLogIn

## Purpose

Navigates the user from the invitation landing page to the standard login view. This is a transitionary step in the invite flow, used when a user arrives via an invite link but chooses to sign in to an existing account instead of creating a new one.

## Invariants

- **Triggers a navigation event** via `this.logInButton.click()`.
- **Waits for `networkidle`** to ensure the login page is fully loaded and interactive before returning control to the test.

## Gotchas

- **Recent introduction** — This method and the surrounding `InviteLandingPage` class were introduced in commit `b59e337` as part of the `/invite/{token}` landing page implementation.

## Cross-cutting concerns

- **Auth**: Navigates the user toward the `LoginPage` flow.
- **Side effects**: Transitioning to the login page clears the current invitation context/token from the active view.

## External consumers

None known.
