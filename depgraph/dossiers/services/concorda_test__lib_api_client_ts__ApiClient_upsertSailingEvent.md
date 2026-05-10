---
node_id: concorda-test::lib/api-client.ts::ApiClient.upsertSailingEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 23fb4cf536e3f0e82456df424d2b4d0afd27454060cf0b2fcacafeab6b22f1d3
status: llm_drafted
---

# ApiClient.upsertSailingEvent

## Purpose
Test-harness wrapper for the captain-side per-boat `SailingEvent` upsert — a thin `PUT /api/events/{eventId}/sailing-event` over the typed `ApiClient`. Three Playwright specs use it to set `dock_time`, `departure_time`, `departure_location`, and `notes` on already-created sailing events so UI assertions can run against a realistic, already-set-up race. It exists so spec authors don't have to drive the captain plan editor through the UI just to reach the state under test (e.g., "logistics filled but no crew → page opens in view mode"). Mirrors prod `eventsApi.upsertSailingEvent` (see `dossiers/services/concorda_web__src_lib_api_ts__eventsApi_upsertSailingEvent.md`); the prod dossier carries the load-bearing semantics — caller-scoped boat resolution, crew-pool/boat agreement, calendar-email side effects.

## Invariants
- The event passed in must already exist with the caller's boat attached (specs always call `createSailingEvent({ boat_uuid })` first); this wrapper is upsert-of-logistics, not a from-zero create.
- Caller must be logged in as the owning captain of the SE — backend resolves the SE row by joining through `BoatCrew` to the caller's owned boat, so a wrong-token call silently targets a different SE or 400s.
- Wrapper returns `Promise<unknown>` and specs do not inspect the body — assertions read state through the UI or follow-up GETs. Don't tighten the return type without auditing callers.

## Gotchas
- Wrapper's TS payload is a hand-curated subset of the real endpoint — `crew_pool_id`, `boat_config_id`, `crew_group_priority`, `arrival_time`, `arrival_location` are NOT exposed even though the backend accepts them. Adding new spec coverage that needs those fields means widening the type here first (or dropping to `rawRequest`). The framing "set crew_pool_id via this wrapper" is aspirational, not current — today specs use `setEventCrewPool` for that.
- `cross-context-crew.spec.ts:163-170` swallows upsert failures with `try/catch` on the theory that "UI assertions will surface any real problem." That mask has hidden regressions before; if a future spec relies on logistics actually persisting, copy the pattern at its peril.
- `dock_time` transitions trigger calendar emails server-side (see prod dossier). Specs that seed crew + invites + logistics in the same run will enqueue real `logistics_set` emails — fine on the test host's mailcatcher, noisy if pointed elsewhere.
- Recent commits on this file are mostly additive (`7d14e73`, `0990b5d`); no reverts touching this method specifically. Keep it that way — the prod-side has the churn.

## Cross-cutting concerns
- Auth: relies on `setToken()` having been called with an owning-captain token; no client-side ownership check.
- Side effect: server-side calendar email dispatch on `dock_time` / logistics transitions — observable on the test host but invisible to the caller.
- TLS: process-wide `NODE_TLS_REJECT_UNAUTHORIZED=0` is set at module load (file:9) so the self-signed test cert is accepted. Don't import `ApiClient` from non-test code.

## External consumers
None. Three in-repo Playwright callers: `tests/events/event-schedule.spec.ts:112` and `:143` (auto-edit-mode heuristics), `tests/dashboard/cross-context-crew.spec.ts:164` (crew-detail-view fixture seeding).

## Open questions
- Should the wrapper accept the full prod payload (`crew_pool_id`, `boat_config_id`, `arrival_*`) so specs don't have to drop to `rawRequest` when coverage expands, or do we want the narrowed surface to keep specs honest about which fields the captain UI actually exposes?
- Worth asserting non-200 instead of swallowing in `cross-context-crew.spec.ts`? The current suppression predates the prod dossier's clarification that crew-pool/boat mismatches 400 — silent failure here could mask exactly that bug.
