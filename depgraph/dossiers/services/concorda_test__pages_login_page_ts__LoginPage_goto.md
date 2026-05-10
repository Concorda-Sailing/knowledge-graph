---
node_id: concorda-test::pages/login.page.ts::LoginPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b94eef6579b64a1b5cc0408b7142e471a18ecbc5690e9114ea422408c5b5cac
status: llm_drafted
---

# LoginPage.goto

## Purpose

Navigates the browser to the `/login` route and serves as the entry point for all authentication-related E2E tests. It is the primary method for resetting the browser state to an unauthenticated view before attempting login or registration flows.

## Invariants

- **Navigates to `/login`** — uses a relative path, assuming the `page` instance is already configured with the correct `baseURL`.
- **Requires a `Page` instance** — the method is an instance method of `LoginPage` and relies on `this.page` being initialized.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; current implementations of `login` and `loginAndWait` are highly dependent on the specific DOM structure of the login page (e.g., `#password`, `#remember-me`) which may change as the UI evolves.

## Cross-cutting concerns

- **Auth**: This is the foundational step for all authenticated flows in the test suite.
- **Side effects**: Successful execution of `loginAndWait` is a prerequisite for testing any protected routes or user-specific dashboards.

## External consumers

- `concorda-test::tests/auth/logout.spec.ts` (via `logout.spec.ts:9`)
