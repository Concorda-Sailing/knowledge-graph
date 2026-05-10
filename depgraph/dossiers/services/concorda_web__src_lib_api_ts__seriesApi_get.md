---
node_id: concorda-web::src/lib/api.ts::seriesApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 48193084b8c74d79284f919cc118cd79bf54cee6a33e1a84706733d478877a79
status: llm_drafted
---

# seriesApi.get

## Purpose

Client-side mirror for fetching a single Series detail — a regatta series is a logical grouping of related races (e.g., a championship or weeknight series) that share a scoring system, qualifier rules, and an OA. `seriesApi.get` returns a `SeriesDetail` (name, dates, scoring_system, qualifier, num_races, race_schedule, organizing_authorities) for one ID. Three call sites consume it: the admin Series detail/edit page (`/admin/events/series/[id]`), and two flows on `/members/regattas` — `RegattaDetailPanel` looks up the parent series to display its banner/links, and `handleAddSingle` in `RegattasPage` uses it to decide whether to prompt "this race or whole series?" when adding a series-child race to a user's schedule. Use this when you need the metadata of the *parent* — for the children, call `seriesApi.listRaces` (or `eventsApi.addRegattas` with a series id, which re-resolves children server-side).

## Invariants

- Endpoint is `GET /api/series/{id}`; backend (`routers/series.py:138`) returns 404 on missing, no auth/role gate (read is open to authenticated members).
- Response shape matches `SeriesRead` Pydantic model — list-typed fields (`scoring_system`, `qualifier`, `race_schedule`) are `Optional[list]`, never strings; the TS type encodes `string[]` but backend will accept any JSON list.
- `organizing_authorities` is hydrated by `_attach_oas` (separate query); `oa_uuid` is the legacy single-OA pointer and may still be set alongside the M2M list.
- `race_schedule` entries are `{date, name?, status?}` plain dicts — they are NOT Regatta records. Children only exist after `generateRaces` (or bundle import) materializes them; use `listRaces` to fetch the actual Regatta rows.
- `id` here is the Series UUID. Regattas reference it via `series_uuid`.

## Gotchas

- Slug regeneration on rename: `update_series` calls `_ensure_unique_slug` whenever `name` changes, so a re-fetch after edit returns a new `slug`. Anything cached by slug needs invalidation.
- `generateRaces` and the season-bundle importer (`scripts/season_bundle/upsert.py`) produce children with *different* slug schemes (name-derived vs. index-based `{slug}-r{idx:02d}`). Don't assume children created via this API match bundle output — series.py:198 explicitly warns the bundle is authoritative.
- On `/members/regattas`, both `RegattaDetailPanel` (line 396) and `handleAddSingle` (line 1058) swallow errors silently (`.catch(() => {})`). A missing/deleted series falls through to a no-series add path rather than surfacing an error — intentional, but easy to misread as "series fetch always succeeds."
- Datetime fields (`start`, `end`, `created`, `modified`) come back as ISO strings; per the codebase convention, render through `lib/datetime.ts` helpers with the org TZ — never raw `Date` methods.

## Cross-cutting concerns

- Auth: `fetchApiAuthenticated` attaches the session cookie; the GET endpoint itself has no role check, so any logged-in member sees series metadata. Mutations (`create`/`update`/`delete`/`generateRaces`) require `_require_manager` + OA scope.
- No websocket/audit emissions on read.
- Side effect: `_attach_oas` issues one extra batched query per call to hydrate organizing authorities — fine for `get`, but if you ever loop this client-side prefer `seriesApi.list`.
- `regattasApi.get` exposes `series_uuid` on regattas; the regattas page chains those two reads. If you change `SeriesDetail`'s shape, audit `RegattaDetailPanel` and the captain/crew prompt flow.

## External consumers

None known. The Expo iOS app does not currently surface series detail. No webhooks, no scheduled jobs reach this endpoint.

## Open questions

- Should `seriesApi.get` proactively include `match_counts` or live "races generated yet?" status, so consumers don't need a second `listRaces` call to decide UI state?
- Read endpoint has no OA scoping — should non-managers see series belonging to OAs they're not a member of? Today: yes. May want to revisit alongside the Tier C scoping work referenced in the org_admin grandfather note.
