---
node_id: concorda-test::tests/auth/login.spec.ts::test@48
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 754d605a7ced76648f8adbe0115ff09a45acba40c5eec15f615f82c8ecf98486
status: current
---

# register link navigates correctly

## Purpose

Verifies that the registration link on the login page correctly redirects the user to the sign-up flow. This test ensures that the navigation path from the authentication entry point to the onboarding/registration page remains intact.

## Invariants

- **Redirect target is `/join`** — The test asserts that clicking the `registerLink` results in a URL match for the registration route.
- **Navigation is triggered by a click** — The test relies on the `loginPage.registerLink` locator to initiate the transition.

## Gotchas

- **Initial scaffolding only** — Per commit `fd0c570`, this file is part of the initial E2E suite scaffolding; tests may be shallow and lack deep integration checks for the registration flow itself.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
