---
node_id: concorda-test::pages/login.page.ts::LoginPage.login
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e6b2f9f2e22d046f4cb47d9082cbfa813a68fd7464b688273589046aa07ef212
status: current
---

# LoginPage.login

## Purpose

The primary method for performing a UI-driven login within the Playwright E2E suite. It populates the email and password fields and triggers the sign-in action. Use `login` for granular control over the flow, but prefer `loginAndWait` if the test requires the application to reach the authenticated state (e.g., navigating to a `/members` URL) before proceeding with assertions.

## Invariants

- **Requires an active page instance.** The method relies on `this.emailInput` and `this.passwordInput` being previously initialized via the constructor.
- **Triggers a navigation event.** Calling `click()` on the sign-in button initiates a network request and a subsequent URL change.
- **Input types are strictly strings.** The method expects raw email and password strings; it does not handle object-based credentials.

## Gotchas

- **Initial setup dependency.** Per commit `fd0c570`, this method is part of the initial scaffolding of the Playwright E2E suite. Ensure that any changes to the login form selectors (like `this.signInButton`) are reflected in the `LoginPage` constructor, or the `login` call will fail with a timeout.

## Cross-cutting concerns

- **Auth**: Directly drives the authenticated state for tests; failure here prevents all downstream authenticated test steps.
- **Side effects**: Affects the session state of the browser instance used in `concorda-test::tests/auth/logout.spec.ts`.

## External consumers

None known.
