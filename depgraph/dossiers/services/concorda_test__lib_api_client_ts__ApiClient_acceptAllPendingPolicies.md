---
node_id: concorda-test::lib/api-client.ts::ApiClient.acceptAllPendingPolicies
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b883eaca4478e16ae50942fb02f6faa2e535bfd4670c06b73ff9701b23a5247
status: current
---

# ApiClient.acceptAllPendingPolicies

## Purpose
Test fixture helper that auto-accepts every pending policy version (TOS, code of conduct, privacy, etc.) for whatever user is currently authenticated on this `ApiClient` instance. It exists so Playwright specs can land on the page they actually want to exercise — an email-deep-link, a co-owner inbox, a crew invite — without first having to script a click-through of the `/policies/accept` modal that the API gates page navigation behind. Mirrors the page's own POST exactly, just without the UI: fetch `/api/policies/me/pending`, and if anything comes back, POST every contract uuid to `/api/policies/me/accept`. Used by 5 specs across `email-link-flows.spec.ts` and `coowner-inbox.spec.ts`, and proxied by `acceptTos()` from `globalSetup` so persisted `storageState` is already past the gate.

## Invariants
- Idempotent and safe to call repeatedly — returns `null` (not an empty success object) when nothing is pending, so callers branching on the return shape must allow null.
- Operates on whoever `this.token` currently authenticates as. There is no user-id parameter; if a test rotates personas mid-run it must `setToken` (or re-`login`) before calling.
- The accept payload key is `contract_uuids` (plural, snake_case) and the values come from the `id` field on each pending policy — not `slug` or `version`. The API rejects any other shape.
- Only accepts policies that come back from `getPendingPolicies()` in the same call. Don't cache the pending list across calls — versions can rotate between login and the gated navigation.

## Gotchas
- Predecessor `acceptTos()` POSTed to a non-existent `/api/auth/accept-tos` and 404'd silently (commit `c70d472`, "accept all pending policies in globalSetup, not bogus /auth/accept-tos"). Every persona's `storageState` was being saved still-gated; tests then failed on the policies modal at unrelated URLs. The fix routed `acceptTos()` through this helper. If you re-introduce a bespoke TOS endpoint, double-check it actually exists in the api router before merging.
- The return-`null`-on-empty branch matters: a callsite that destructured `{ accepted }` would crash on a clean DB. Keep the union return type.
- `getPendingPolicies()` requires auth; calling this before `login()` throws a 401 from `request<T>` rather than a friendly error. Ordering in test setup: login → acceptAllPendingPolicies → save state.
- The helper does not re-fetch `/auth/me` afterward, so any in-memory user object the caller is holding will still claim policies are pending until refreshed. Most consumers don't care because they navigate away.

## Cross-cutting concerns
- Auth: requires a valid bearer token on `this.token`; mutates server-side policy-acceptance state for that person (audit rows are written by the api side — this client doesn't see them).
- Side effect on other features: clearing the policy gate is what lets `/api/invite/respond`-bearing email links resolve directly to their target page in the email-link-flow specs; if this stops working those specs will start failing on a redirect to `/policies/accept` rather than the assertion they care about.
- Not rate-limited at the client; the underlying api endpoint is. In practice each persona only calls it once per global-setup run, so headroom is fine.
- No websocket / no background-job interactions.

## External consumers
None outside the `concorda-test` repo. The production web app and the Expo iOS client both go through their own `/policies/accept` UI; this helper is strictly a test-harness shortcut.

## Open questions
- Should `acceptTos()` be deleted now that it's a one-line passthrough, or kept as a stable name for older spec call-sites? Currently kept for compatibility but no spec on `main` still calls it directly.
- If/when policy acceptance gains required attestations (e.g. age confirmation) beyond the contract uuid, this helper's payload shape will need to grow — worth revisiting before that ships rather than after specs break.
