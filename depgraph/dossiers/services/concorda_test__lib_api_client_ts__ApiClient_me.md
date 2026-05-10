---
node_id: concorda-test::lib/api-client.ts::ApiClient.me
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a44abe44cd91ebc177f1fdc16e1cf2abad680b438f234a7e73a1c96a4d4de393
status: current
---

# ApiClient.me

## Purpose

Test-harness wrapper for the lightweight "who am I" endpoint (`GET /api/auth/me`). Returns id / email / name / permissions / pending_policy_acceptances — the same payload the web client uses to bootstrap a session. Specs use it to (1) assert login succeeded against a known persona and (2) read the resulting `id` so they can wire that user into subsequent test setup (crew pools, approval votes, invite targets). 9 specs consume it (more than the dependent count rounded; almost every login flow ends with `(await x.me()).id` to capture identity).

## Invariants

- Endpoint is `GET /api/auth/me`; requires `Authorization: Bearer <token>` set via `setToken` / `login`. 401 without a token, 404 if the Person row is gone.
- Wrapper return type is **narrow**: `{id, email, first_name, last_name}`. Real `UserResponse` from the API also includes `picture_url`, `memberships[]`, `permissions[]`, `pending_policy_acceptances[]`. Don't widen at runtime — the type is intentionally trimmed to what specs assert on.
- Token is single-state on `ApiClient`; calling `me()` after switching personas via `setToken` returns the new persona's identity, not the original one. Specs interleaving personas via one client must `setToken` before each `me()`.
- No params, no side effects — read-only.

## Gotchas

- **Type drift vs. API**: `permissions` and `pending_policy_acceptances` are present on the wire but absent from the wrapper's TS type. A spec that needs permission gating should call `acceptAllPendingPolicies` or hit the dedicated permission endpoint rather than expecting them here. Adding them to this type is fine; assuming they exist without widening will produce `undefined` at runtime.
- **Used as id-capture, not assertion**: most call sites are `const { id } = await api.me()`. Specs rarely assert on email/name. If the response shape ever drops `id` (won't happen — it's the load-bearing field), every dependent spec breaks at the destructure, not at a clear error site.
- **No retry**: `request<T>` throws on any non-2xx. A 502 during a deploy window flakes specs that call this in `beforeAll`. By design — don't add retry here, fix the deploy timing.
- **Internal consumer**: `getUserIdByEmail()` (line 541 of this file) uses `me()` as a fallback path, swapping the token mid-flight and restoring it. Any future callsite that runs `me()` in parallel with that helper would race on the shared token state — the harness is single-threaded today.

## Cross-cutting concerns

- **Auth**: bearer token required. No org scoping. Permissions are flattened across every UserRole the user holds.
- **TLS**: process-wide `NODE_TLS_REJECT_UNAUTHORIZED=0` from module load — never run this client against staging/prod.
- **No rate limiting** distinct from global API limits.
- **Side effects**: pure read; no audit, no broadcast.

## External consumers

None. Test-harness only. The 9 dependent specs span auth (login round-trip + email-link flows), boats (co-owner inbox/shared-events/crew-badge), API-only flows (approvals, schedule-crew-options-gating), dashboard (cross-context-crew), and events (event-schedule).

## Open questions

- Should the type widen to include `permissions` so specs can gate without a separate fetch? Five specs would simplify if they could read both in one call.
- The `getUserIdByEmail` token-swap pattern is fragile — worth a typed admin-only `/api/admin/users/by-email` endpoint so the helper doesn't have to log in/out as the target user just to read their id.
