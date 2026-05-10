---
node_id: concorda-test::lib/api-client.ts::ApiClient.getPendingPolicies
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d2fc0aaf823ebd1cce8d4cf44710da23a02611c6d5da83f1f174e81cf778cd83
status: llm_drafted
---

# ApiClient.getPendingPolicies

## Purpose

Fetches the list of Terms of Service (TOS) or legal policies that the authenticated user has not yet acknowledged. This is a read-only helper used to determine if a user is "gated" by unaccepted terms. It is the prerequisite call for `acceptAllPendingPolicies`, which is used in E2E tests to bypass UI-based TOS prompts that would otherwise block navigation to protected routes.

## Invariants

- **HTTP Method:** `GET`
- **Endpoint Path:** `/api/policies/me/pending`
- **Return Shape:** An array of objects containing `{ id: string; slug: string; name: string; version: string }`.
- **Auth Requirement:** Requires a valid bearer token; the `ApiClient` instance must be authenticated.

## Gotchas

- **Avoid manual UI interaction for TOS:** Per commit `c70d472`, the test suite now uses `acceptAllPendingPolicies` in `globalSetup` to ensure a freshly-rotated TOS version doesn't block the test flow when arriving at an email link. If you are writing a test that hits a page protected by a new policy, ensure you call the acceptance logic rather than trying to click through the UI.

## Cross-cutting concerns

- **Auth**: Depends on the `this.token` established via `ApiClient.login`.
- **Side effects**: Used by `acceptAllPendingPolicies` to clear the pending state, which unblocks access to protected dashboard routes.

## External consumers

- `concorda-test::tests/auth/policies-gate.spec.ts`
