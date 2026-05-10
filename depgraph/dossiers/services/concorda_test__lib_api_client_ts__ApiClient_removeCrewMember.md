---
node_id: concorda-test::lib/api-client.ts::ApiClient.removeCrewMember
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3560e59810ce89c72b09ebd2ce8d1319925f276f74d433294a841d2a4bfbcb51
status: llm_drafted
---

# ApiClient.removeCrewMember

## Purpose
Test-harness wrapper for an owner removing a crew member from a boat — issues `DELETE /api/boats/{boat_id}/crew/{crew_id}` via the typed `ApiClient`. Mirrors prod `boatApi.removeCrew` so Playwright specs can exercise the same authz path the UI takes, but its dominant role here is **cleanup-between-tests idempotence**: 5 spec sites call it (most wrapped in `.catch(() => {})`) inside `test.beforeEach`/`afterEach`/setup helpers to guarantee a known-empty BoatCrew slot before seeding the next scenario. Future Claude: pick this when a test needs to assert "owner can remove this crew row" OR when it needs to scrub a leftover BoatCrew/PendingCrewInvite row left by a prior run on the persistent test host. Do NOT reach for it as a status-flip — same as prod, this is a hard delete.

## Invariants
- The `crewId` slot accepts both a `BoatCrew.id` and a `PendingCrewInvite.id`; server resolves which. Tests don't need to branch on kind, but they DO need to fetch the row id first via `getBoatCrew(boatId)` before calling — there is no email-based remove.
- Caller must be authenticated as the boat owner (token set via `setToken`/`login`); a 403 will surface as a thrown `Error` from the `request<T>` helper. Cleanup sites suppress this with `.catch(() => {})` because "not present" and "not owner of nothing" are both acceptable end states.
- Returns `void` (204 path of `request<T>`). Specs must NOT chain `.then(row => ...)` — there's no body.
- Hits the same persistent test host as every other ApiClient method (`API_URL`, TLS verification disabled at module load). This is shared mutable state across the whole suite; ordering between specs that touch the same boat is not guaranteed unless they explicitly seed/clean.

## Gotchas
- `0990b5d` (the commit that added the email-link-flow specs and indirectly the heaviest user of this method) leaned on `.catch(() => {})` cleanup because re-runs on the test host frequently leave Carol/Dan rows from a prior failed assertion. Removing the `.catch` to "see what's failing" will turn flake into hard fail and obscure the real assertion error.
- The wrapper happily 404s for a stale id captured before a prior cleanup ran — failures here are silent in spec cleanup paths and load-bearing in spec assertion paths. Don't add a "smart" 404-as-success retrofit at this layer; the prod mirror doesn't do that and tests would diverge.
- Permanent delete with no audit trail (same as prod). A spec that removes and then re-invites the same email gets a brand new BoatCrew row — do not write assertions assuming row id stability across remove/re-add.
- The future My Crew delete-guard work (per `project_my_crew_delete_guard`) will likely add a 409 path on the server. Specs that today rely on unconditional success will need updating; the cleanup sites (`.catch`) are forward-compatible, the assertion sites are not.

## Cross-cutting concerns
- **Auth:** Bearer token from `ApiClient.token`; no cookie path (the prod mirror uses session cookies — this is the test-side divergence). Token must be the boat owner's.
- **Realtime:** Server emits `BOAT_CREW_UPDATED` SSE on success. The Playwright UI specs don't subscribe directly, but any spec that calls `removeCrewMember` and then reloads a UI page expecting the row gone is implicitly relying on the page's SSE/refetch — flake here usually traces to a stale-cache fetch, not the DELETE itself.
- **Side effects:** Same as prod — orphans `EventCrew` rows, crew-pool memberships, and open invites referencing the same person. Tests that exercise event-crew flows AFTER calling `removeCrewMember` may see ghost rows; seed event crew explicitly rather than assuming cleanup cascaded.
- **No rate limit** distinct from global auth limits.

## External consumers
None. Test-harness only. Not exported beyond the `concorda-test` repo.

## Open questions
- Cleanup sites currently swallow all errors via `.catch(() => {})`. Should the harness distinguish "row not found, fine" (404) from "auth broken" (401/403) so a misconfigured test token surfaces loudly instead of looking like an idempotent no-op? Today a token regression in `globalSetup` would make every cleanup silently no-op and tests would only fail later at assertion time.
- When the My Crew delete-guard lands server-side, does the test harness want a `removeCrewMemberForce` escape hatch for cleanup, or do specs adapt to the new precondition? Answer probably depends on whether the guard is warn-only or hard-block.
