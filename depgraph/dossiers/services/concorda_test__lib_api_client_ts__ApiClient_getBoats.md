---
node_id: concorda-test::lib/api-client.ts::ApiClient.getBoats
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9ded4cb9e21a100bb6d4e465708f8c09b6b1c8a014511c1bf3f5681908dc8256
status: llm_drafted
---

# ApiClient.getBoats

## Purpose

Test-harness wrapper for `GET /api/profile/boats` — the owned-only boat list for the authenticated test user. Mirrors prod `profileApi.getBoats` exactly: same endpoint, same `BoatCrew.role='owner' AND status='active'` semantics, same "owned-only, not crewed" return contract. Used by 5 Playwright specs to assert post-registration ownership state ("Bob just became an owner — does he show up in his own boats list?") and to look up boat ids by sail number after seeding so subsequent steps (co-owner invites, crew invites, sailing-event setup) have a real `boat_uuid` to work with. The return type here is intentionally narrower than prod's `BoatRead` (`{id, name}` only) — tests only use these two fields and tightening the type keeps spec assertions honest.

## Invariants

- Endpoint string is `/api/profile/boats`, no params, GET. If prod `profileApi.getBoats` ever changes URL or shape, this wrapper must change in lockstep or every dependent spec silently breaks.
- "Owned" means `role='owner' AND status='active'` — same join as prod. Crew-only seeded users get `[]` here; specs that need crewed boats must use `getMyCrewData` (`/api/profile/crew`), not this method.
- Auth is bearer-token via `setToken` / `login`; calling without a prior login throws on the API side (401 → `Error` from `request`). Specs expect this and rely on it for negative-path assertions.
- Return type stays `Array<{id; name}>`. Specs destructure these two fields; widening to full `BoatRead` is fine, narrowing further is not.

## Gotchas

- **Owned-only, not "boats I crew on"** — same trap as prod. `coowner-inbox.spec.ts::findBobBoat` previously had a moment of confusion when the spec author expected co-owner invitees to show up here pre-acceptance; they don't. The boat appears in `getBoats` only after the invite is accepted and `BoatCrew.status` flips to `active`.
- **Sail-number lookups iterate the full list** — specs typically do `boats.find(b => b.sail_number === '...')`, but the current return type doesn't include `sail_number`. In practice specs cast to `any` or re-fetch via `/api/profile/crew`. If sail-number filtering becomes common, widen the return type rather than perpetuating the cast.
- **No retry on transient failure** — `request` throws on any non-2xx; specs that hit this during a server restart or migration window fail loudly. That's by design (don't paper over real bugs) but explains intermittent "API GET /api/profile/boats failed (502)" flakes during deploy windows.
- **TLS verification disabled process-wide** (`NODE_TLS_REJECT_UNAUTHORIZED=0` at module top). Fine for the test host's self-signed cert, but means this client must never be aimed at prod by accident — there's no cert-pinning safety net.

## Cross-cutting concerns

- **Auth**: bearer token only; no org scoping. A test persona seeded in multiple orgs sees boats across all of them.
- **WebSocket**: this client doesn't subscribe to anything. Each call is a fresh fetch — if a previous test step inserted a boat, the next `getBoats` call sees it without any invalidation dance. (Prod's `useBoats` hook does that work; tests don't need it.)
- **No caching, no dedup**: every call is a round-trip. Specs that want a stable id should call once and hold the value, not call repeatedly.
- **Side effects on other specs**: nothing here mutates state, but the value returned drives boat-id selection for downstream POST/PUT calls (co-owner invite, crew invite, sailing-event creation). A regression that returns the wrong set of boats cascades into mis-seeded test fixtures — the failure surfaces several steps later, not here.

## External consumers

None. Test-only code, never shipped. The 5 Playwright specs listed in the dependents block are the entire consumer set.

## Open questions

- Should this widen to `Array<{id; name; sail_number}>` so specs can stop casting to `any` for the common sail-number lookup pattern? Prod returns full `BoatRead` already; the test wrapper is the one being stingy.
- Worth a `getBoatBySailNumber(sail: string)` convenience method on `ApiClient`? Three of the five dependents do the same `find` dance inline.
