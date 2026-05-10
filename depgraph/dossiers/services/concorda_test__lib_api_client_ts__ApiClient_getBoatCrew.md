---
node_id: concorda-test::lib/api-client.ts::ApiClient.getBoatCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ef20e1dc0d844691fe51cfe5985f63baa24c17e84cb06df4c75b7695cc1e1be8
status: current
---

# ApiClient.getBoatCrew

## Purpose
Test-harness wrapper around `GET /api/boats/{id}/crew` — the test-suite `ApiClient` method that 9 Playwright specs use to assert crew state after mutations driven through the UI or other API calls. Contract mirrors `boatApi.getCrew` (see `boatApi.getDetail` dossier for the prod-side surface). The harness uses it for three jobs: (1) idempotence pre-cleanup — find a stale crew row from a prior run and delete it before re-inviting; (2) post-mutation assertion under `expect.poll(...)` — read the row's `status` until it flips to `active`/`declined`/`accepted`; (3) crew-id lookup — translate `(boat_id, person_uuid)` into the `BoatCrew.id` an emailed accept/decline URL embeds.

## Invariants
- Returned shape is `{ id, person_uuid, status, role }[]`. `id` is the `BoatCrew` row id (per-invite, not stable across re-invites). Specs key off this for idempotence and for matching `/members/invite/accept/{id}` URLs.
- Caller must `setToken(bobToken)` first — the endpoint 403s for non-crew, so seed-owner Bob is the standard reader. Switching to a recipient token (Carol/Dan) before this call will fail mid-spec.
- Status values the suite asserts on: `invited`, `active`, `declined` (boat crew); `accepted` shows up only on the parallel `getEventCrew` path.

## Gotchas
- Recent commit `0990b5d` added the email-link flows that read `getBoatCrew` 11 times across 5 tests; an unstable response shape (e.g. renaming `person_uuid` → `user_id`) would break all of them silently — no schema validation here, just `Array<...>` with an inline type.
- `ApiClient` is shared, single-token state. Call sites repeatedly `api.setToken(bobToken)` right before `getBoatCrew` because intervening UI/login steps mutate the same client. Forgetting this read-as-Bob switch is the #1 way these specs flake.
- The test host is long-lived (`test.mbs`, 10.0.1.140) — DB is not wiped between specs. That's why every consumer pattern is "fetch crew → find stale row → remove → invite fresh." Removing the pre-cleanup makes the second run fail because a stale `active` row blocks a new `invited` row.
- Cleanup blocks at the end of each test re-call `getBoatCrew` to find and delete the row they created. If `removeCrewMember` is rate-limited or 500s, the next run inherits that row and the idempotence prelude saves the suite. Don't remove the prelude even if cleanup looks complete.
- Self-signed TLS is bypassed process-wide via `NODE_TLS_REJECT_UNAUTHORIZED=0` at `api-client.ts:9`. Acceptable here, but means this client must never be repurposed against staging/prod.

## Cross-cutting concerns
- Auth: bearer token via `Authorization: Bearer <jwt>`; obtained from `api.login(...)`. No cookie/session — independent of UI session lifecycle, which is why specs can drive UI as one persona and read API state as another via two clients (or one client with `setToken` toggles).
- No websocket or polling integration on the test side — assertions are explicit `expect.poll` loops with 5s timeouts, not WS-driven freshness.
- No rate-limit awareness; suite assumes the API limiter (single-uvicorn, in-memory) won't trip during normal test pacing. If it does, the `expect.poll` retries amplify the problem.
- No side effects.

## External consumers
None. This is internal to the `concorda-test` Playwright suite.

## Open questions
- Worth promoting the `(boatId, personUuid) → crewId` lookup (today open-coded in `findCarolCrewId` and the `inviteDan`/`inviteCarol` preludes) into an `ApiClient.findBoatCrewRow` helper? Five specs have near-identical copies.
- The inline return type drifts from the prod `boatApi.getCrew` shape — no shared type. Acceptable for a thin harness, but a prod-side rename will only surface as a runtime `undefined` on `c.person_uuid`.
