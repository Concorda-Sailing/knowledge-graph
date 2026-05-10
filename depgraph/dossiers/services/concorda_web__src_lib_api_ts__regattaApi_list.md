---
node_id: concorda-web::src/lib/api.ts::regattaApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d21513d00210bcba9c004b07e979a593c80e82192a573e9d84430cb95f50bd59
status: llm_drafted
---

# regattaApi.list

## Purpose
Client-side mirror of `GET /api/regattas` — a flat list of every regatta visible to the caller, each row carrying embedded `match_counts` from `_attach_counts`. Powers the public-facing regattas browse page (`/members/regattas`), the admin race calendar (`/members/admin/events/races`), and the awards page's series-context lookup. Despite the natural "filtered list" framing, the function takes **no arguments** and returns the full set; year/region/scoring/qualifier filtering, sorting, and month grouping are all done client-side in each consumer (see `monthTabs` in races/page.tsx, the filter chips on regattas/page.tsx). The handler does accept `region_uuid` and `course_type` query params, but no caller wires them — adding filters here would be a server-side optimization for a problem nobody currently has.

## Invariants
- Returns `RegattaDetail[]`, never null. Empty list on no-data; consumers `.catch(() => [])` to absorb auth/network failures.
- Server orders by `Regatta.start.desc()` — newest first. Consumers that re-sort (admin races page) must not assume ascending input.
- Each row includes `match_counts` (boats_registered / boats_looking / crew_looking) computed in a single bulk pass via `_attach_counts` — N+1 risk if you ever switch to per-row enrichment.
- Visibility is gated upstream by Tier C cross-org scoping (`058aa8c`): a Mercury Bay member won't see Hingham-only regattas. This is enforced at row-level in the query path, not in the response shape.

## Gotchas
- The handler signature looks filterable (`region_uuid`, `course_type` query params) but **no consumer passes either**. If you "add filtering," check that you're not duplicating client-side filter logic that already works — and that you don't break the awards/admin consumers that need the full set.
- All three consumers fetch the entire list on mount with no pagination. Today's volume is fine; once historical regattas accumulate over multiple seasons, the admin races page will feel it first (it builds month tabs from every row).
- `RegattaDetail` is a heavy shape — pulling the full list for the awards page just to map `series_uuid` is wasteful. A leaner `regattaApi.listForSeries` or a server-side join would be cleaner if awards becomes hot.
- Recent `b67d359 fix(regattas): drive Accepting-Crew badge from per-race toggle` moved accepting-crew off regatta-level fields onto per-`SailingEvent` toggles — list rows do **not** tell you whether crew is being accepted; that requires `getMatchRoster` or `mySchedule` cross-reference.

## Cross-cutting concerns
- **Auth**: `fetchApiAuthenticated` — bearer token required. Anonymous browse goes through a different shape, not this one.
- **Org scoping**: Tier C visibility filter applies; admins in org A do not see private regattas in org B.
- **Audit / websocket**: pure read, no audit-log write, no broadcast.
- **Caching**: none server-side; consumers refetch on mount and after delete (`load()` in races/page.tsx). React Query is not in play here.
- **Coupling to `match_counts`**: the same `_attach_counts` helper feeds `regattaApi.get` and the slug lookup — divergence between list and detail counts implies a bug there, not in callers.

## External consumers
None known. No Expo app calls, no scheduled jobs, no webhooks. The `concorda-test` harness exercises it via `ApiClient.listRegattas` (test-only).

## Open questions
- Should the awards page's "regatta belongs to which series" lookup move server-side rather than fetching every regatta to filter by `series_uuid` client-side?
- Once historical seasons accumulate, do we paginate, or move to a `?since=YYYY-MM-DD` filter? The handler is already shaped for query-param filtering — adoption is the gap.
