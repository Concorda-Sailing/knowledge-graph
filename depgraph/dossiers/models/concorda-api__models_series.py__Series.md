---
node_id: concorda-api::models/series.py::Series
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9f3c50f149a67cc08a4de9fb71af67f3fafb2e5576b296489db098dd2fb3f919
status: current
---

# Series

## Purpose

Backend SQLAlchemy model for a regatta series — a collection of related races sharing scoring system, qualifier rules, organizing authorities (OAs), and metadata. Children are `Regatta` rows that reference their parent via `series_uuid`. The `race_schedule` JSON list of `{date, name?, status?}` entries is a pre-generated child manifest expanded into actual `Regatta` records by the `POST /api/series/{id}/generate-races` endpoint. Series is the unit a member subscribes to via "my schedule" and the unit OAs publish/administer; race-level details live on the child `Regatta` rows. Seven dependents, all in `routers/series.py`.

## Invariants

- `name` is the only required field; everything else (including `slug`, `start`, `end`) may be null. Bundle imports populate slug/start/end; hand-authored series can omit them.
- `slug` is globally unique when set. `_ensure_unique_slug` gates inserts in the router.
- OA membership lives in the `OrganizationSeries` join table, **not** in the `oa_uuid` column. `oa_uuid` is legacy and kept for SQLite compat after the schema redesign (`ee82e42`); writes go through `set_series_oas`/`get_series_oas`.
- `race_schedule` entries must carry a parseable `date` (ISO or `YYYY-MM-DD`) to expand into a Regatta; entries without a date are skipped, not errored.
- `start`/`end` are tz-aware via `UtcDateTime` (since `5a7ff17`). Pre-2026-05-06 rows may be 4–5h off and need hand-fixing — do not assume naive=UTC for old data.
- `type="Series"` is forced in `__init__` (BaseModel polymorphic discriminator). Don't bypass the constructor.

## Gotchas

- **Two slug strategies coexist for child regattas.** `generate_races` uses name-derived slugs via `_generate_slug`; the bundle importer (`scripts/season_bundle/upsert.py`) uses index-based `{slug}-r{idx:02d}`. Re-running `generate_races` on a bundle-imported series creates orphan children the bundle will not clean up. The router header comment (lines 198–204) flags this — bundle is authoritative; the endpoint is a manual fallback only. (`8652d95` flagged the mismatch.)
- `generate_races` copies `s.scoring_system and None` into `Regatta.classes` — that's an intentional no-op (classes come from per-race NOR), not a bug. Don't "fix" it to copy scoring_system into classes.
- `description` is `Text`, with a `# future: JSON` comment. `c96486e` reverted an attempted JSON migration; treat as plain text until a real migration ships.
- `qualifier` and `race_schedule` are marked legacy in the source but are still actively read by `generate_races` and the `seriesApi` PUT/POST round-trip. "Legacy" here means "predates the relationship-table redesign," not "unused" — don't drop the columns.
- Children are not cascaded. Deleting a Series leaves its child Regattas with a dangling `series_uuid` (no FK in SQLite). The DELETE route does not currently warn or block — caller must clean up children manually.

## Cross-cutting concerns

- **Auth scoping:** mutations require `_require_manager` and `_require_oa_scope` — caller must administer every OA in `organizing_authority_uuids`. Tier-C cross-org enforcement landed in `058aa8c`; respect it on any new endpoint that touches Series.
- **OA join:** all reads/writes that care about OA association go through `services/organizing_authorities` (`get_series_oas`, `set_series_oas`, `set_regatta_oas`), not the legacy `oa_uuid` column.
- **Child propagation:** `generate_races` copies `oa_uuid`, `qualifier`, `scoring_system`, `description` to each child Regatta and re-applies the OA join via `set_regatta_oas`. Adding a new "series-level" field that should propagate to children means editing this loop.
- **My-schedule coupling:** `fdc87b4` added series-aware my-schedule filtering. Members subscribe to a series; their schedule view aggregates that series' Regattas. Renaming/removing a Series field used in the schedule projection breaks that view.

## External consumers

- `concorda-web` via `seriesApi` (list/get/create/update/delete/generateRaces/listRaces) — see sibling `seriesApi.get` dossier.
- `scripts/season_bundle/upsert.py` — authoritative bulk importer; bypasses the API and writes Series + child Regattas directly with index-based slugs.
- No webhooks, no scheduled jobs, no Expo app reads (the iOS app currently consumes events/regattas, not series directly).

## Open questions

- Should DELETE on Series cascade to child Regattas, or refuse when children exist? Currently it does neither.
- Is `description` ever migrating to JSON? The `# future: JSON` comment has survived several commits; either commit to the migration or drop the comment.
- `qualifier` is a free-form JSON list copied verbatim into each child Regatta. No schema is enforced. Worth pinning a Pydantic shape before another consumer reads it.
