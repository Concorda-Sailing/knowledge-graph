---
node_id: concorda-test::lib/api-client.ts::ApiClient.acceptTos
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 14bc477f6c896576971297c317372091507ce828e78e92adad44fe77f57c1510
status: current
---

# ApiClient.acceptTos

## Purpose
Thin compatibility shim around `acceptAllPendingPolicies()`. Exposes the historical name `acceptTos` so older test setup code and specs that predate the multi-policy world keep compiling, while the actual work — fetching pending policies and POSTing their ids to `/api/policies/me/accept` — lives in one place. Used by `globalSetup` (to dismiss the policy gate before storageState is persisted) and by four specs that arrive at the app via fresh login or email link and would otherwise be redirected to `/policies/accept`.

## Invariants
- Must remain a no-arg, void-returning method. All five call sites invoke it as `await api.acceptTos()` with no parameters and ignore the return.
- Must continue to delegate to `acceptAllPendingPolicies()` rather than calling a single endpoint directly. The previous direct-endpoint implementation 404'd silently (see Gotchas).
- Idempotent: callable on a freshly-seeded persona with nothing pending and on one mid-rotation; never throws on "nothing to accept".
- Requires `this.token` to be set (call after `login()`). Anonymous use will 401 from the underlying `/api/policies/me/pending` GET.

## Gotchas
- `c70d472` is the load-bearing commit: this used to POST to `/api/auth/accept-tos`, an endpoint that does not exist. The 404 was swallowed, every persona's `storageState` was persisted with the policy gate still active, and tests intermittently failed at the gate after any TOS version bump. If you "simplify" this back to a single-endpoint call, restore that bug.
- Name is misleading. It accepts **every** pending policy (TOS, code of conduct, future additions), not just TOS. Don't add a slug/id parameter expecting it to scope down — callers don't pass one and the underlying helper bulk-accepts by design. If a single-policy variant is genuinely needed, add a new method (`acceptPolicy(slug, version)`) rather than overloading this one.
- Order matters in `generateAuthState`: must run after `login()` and before `context.storageState()` is written, otherwise the persisted session lands on `/policies/accept` on first navigation.
- `acceptAllPendingPolicies()` returns `null` when nothing is pending; this wrapper discards that. Callers that need to know whether anything was accepted should call the underlying method directly.

## Cross-cutting concerns
- Auth: requires bearer token; mutates server-side `PolicyAcceptance` rows for the current user.
- Side effects: clears the policy gate for that user across all subsequent requests in the test run, including persisted storageState reused by other specs in the project. A test that wants to assert the gate is visible must use a fresh persona that has *not* been through `generateAuthState`.
- No rate-limit or websocket implications.
- Audit trail: each accepted contract writes a `PolicyAcceptance` row; tests that count rows in that table need to account for setup-time acceptance.

## External consumers
None. Test-only helper; not shipped in any runtime artifact.

## Open questions
- Worth deprecating the name outright? Five call sites is small enough to rename to `acceptAllPolicies` in one pass and drop the alias. Leaving it for now because the name still reads sensibly at call sites and the indirection cost is zero.
- The framing prompt described this as a "single-policy acceptance variant by slug+id." That method does not exist today — `acceptTos` is a zero-arg alias. If a single-policy variant is wanted, it would need to be added; this dossier reflects what the code actually does.
