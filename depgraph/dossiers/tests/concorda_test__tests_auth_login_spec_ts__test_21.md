---
node_id: concorda-test::tests/auth/login.spec.ts::test@21
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d2934138529d11568b6e4faeb6f40b79b9ff6f049bbf4eedc0931cd2262a912
status: llm_drafted
---

# successful login redirects to dashboard

## Purpose

Verifies the successful authentication redirect flow. It ensures that providing valid credentials via the `loginPage.login` helper results in a successful navigation to the `/members` dashboard route.

## Invariants

- **Redirect destination** — A successful login must result in a URL match for the `/members` pattern.
- **Timeout threshold** — The test relies on a 15-second timeout for `page.waitForURL` to account for network latency during the redirect.
- **Credential source** — Uses the `USERS.alice` object from the test data library to drive the login attempt.

## Gotchas

- **Redirect pattern sensitivity** — The test uses a glob pattern `**/members**` for `waitForURL`. If the dashboard routing structure changes (e.g., to `/dashboard/members`), this test will fail despite a successful login.

## Cross-cutting concerns

- **Auth**: Uses `loginPage.login` which interacts with the authentication API.
- **Side effects**: Successful execution validates the core path for the `/members` dashboard entry point.

## External consumers

None known.
