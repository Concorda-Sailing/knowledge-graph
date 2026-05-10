---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::assertHostedOnTest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b053695937f95bac150250464f1d7e3140db6877520048f3119904eff848423c
status: llm_drafted
---

# assertHostedOnTest

## Purpose

A utility function used to validate that an email-driven decision URL (accept/decline) is correctly hosted on the test environment. It ensures that the generated link matches the expected pattern for the `/members/invite/{action}/{id}` endpoint, preventing tests from passing if the URL structure or host is incorrect.

## Invariants

- **Requires a `url` string** to validate against the base URL.
- **Requires an `action` argument** which must be exactly `'accept'` or `'decline'`.
- **Matches against `BASE_URL`** with the trailing slash stripped to ensure the prefix is robust.
- **Expects a specific path structure**: `${BASE_URL}/members/invite/${action}/`.

## Gotchas

- **Strict prefix matching**: The function uses `.toContain()` rather than an exact match, but it relies on the `expectedPrefix` being correctly constructed from `BASE_URL`. If the `BASE_URL` is modified in the test setup, this function's validation logic will shift accordingly.

## Cross-cutting concerns

- **Auth**: None. This is a pure URL string validation helper.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
