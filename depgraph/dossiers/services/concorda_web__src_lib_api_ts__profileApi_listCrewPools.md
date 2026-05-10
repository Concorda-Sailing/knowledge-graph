---
node_id: concorda-web::src/lib/api.ts::profileApi.listCrewPools
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5a106bf10605d29a73e4fdfc8239bda06a4d1ce08b4f4bf951a7f6a8c57c18b6
status: llm_drafted
---

# profileApi.listCrewPools

## Purpose

Client-side mirror for `GET /api/profile/boats/{boat_id}/crew-pools` — fetches the named CrewPool groupings for a single boat (e.g. "My Distance Crew", "Wednesday Night Crew"). Used by surfaces that need to *pre-fill an invite list* from a saved grouping rather than re-pick people each time: the My Crew pool-management tab, the schedule new-event boat picker (`event-plan-panel`), the per-event crew picker (`event-crew-card`), and the regattas captain form. A future Claude editing this should know: pools are user-curated *shortcuts* into the crew picker, not a permission/ACL layer.

## Invariants

- Route is **boat-scoped**, not person-scoped: takes a `boatId` and returns pools belonging to that boat. The `boat_uuid` column on `CrewPool` is the source of truth.
- Backend gates with `_require_boat_owner(boat_id, ...)` — only the boat owner can list. Non-owners get 403, which all four callers swallow with `.catch(() => [])`.
- Returns `CrewPool[]` ordered by `name` (alphabetical, server-side). Callers that show pools in UI rely on this order; don't move sorting client-side without checking each consumer.
- `member_ids` is a `string[]` of person UUIDs in **click/selection order** — first id = priority 1. This ordering is load-bearing for invite dispatch (see `project_invite_priority_order`); never re-sort `member_ids` alphabetically or by name.
- Pools with the same name on different boats are independent rows. Don't dedupe by name across boats.

## Gotchas

- **Domain model was reversed on 2026-05-03** from person-owned to boat-scoped. The `CrewPool` entity is boat-scoped via `CrewPool.boat_uuid`, matching the `BoatConfig` pattern. Distinct from "My Crew" (the dashboard concept), which IS person-centric. If a spec asks for person-scoped pools, that is a model change and needs explicit design, not a quiet refactor here.
- All four consumers `.catch(() => [])` on failure — a 403 (non-owner) and a 500 are indistinguishable to the UI. If you add error semantics (e.g. "you no longer own this boat"), update callers; otherwise silent degradation continues.
- `my-crew-tab.tsx` calls this in a `Promise.all` over `owned_boats` — N+1 by design. If a user has many boats this could grow; a `GET /api/profile/crew-pools` aggregate endpoint has been hinted at but doesn't exist yet.
- `setCrewPool` / `suggestCrewPool` on `eventsApi` (lines 481, 518) operate on a *different* concept (the event's chosen pool snapshot) — don't confuse them with these CRUD endpoints.

## Cross-cutting concerns

- **Auth**: requires authenticated session + boat ownership; no public/peer-readable variant exists.
- **Privacy**: pool contents reveal crew identities. Today only the owner can read, which sidesteps the `feedback_crew_visibility_privacy` rule, but if non-owner read is ever added, peer identities must respect resume-published gating.
- **Side effects**: read-only. Mutations live on `createCrewPool` / `updateCrewPool` / `deleteCrewPool` and on `SailingEvent.crew_pool_id` writes (which the API validates: pool must belong to the event's boat).
- **Audit / websocket**: none on the read path.

## External consumers

None known. No mobile app surface, no scheduled job, no webhook reads this. The Expo iOS app does not currently call crew-pool endpoints.

## Open questions

- Should there be an aggregate `GET /api/profile/crew-pools` returning `{ boat_id, pools[] }[]` to collapse the N+1 in `my-crew-tab`?
- `project_my_crew_delete_guard` (future) — should `deleteCrewPool` block / warn when the pool is referenced by an upcoming event's `crew_pool_id`? Not enforced today.
