---
node_id: concorda-api::models/regatta.py::Regatta
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 31f181e8e8e6a3ddcd56255ee27d8db6e61fd02fb1769e442bf23e0a801f14bb
status: llm_drafted
---

# Regatta

## Purpose

`Regatta` is the metadata-and-identity layer for racing events: name, slug, dates, location, course, scoring system, qualifier tags, organizing authority links. It is *not* the calendar surface — that's `Event` with `category="regatta"` and `regatta_id` pointing here. A regatta says "this race exists in the world, here are its rules and references"; the matching `Event` row(s) say "this race is on the schedule on this date." A single multi-day regatta typically has one `Regatta` row and multiple `Event` rows (one per race day), tied together by `Event.regatta_id`. Match counts, NOR documents, organizing authorities, and per-person intents (`RegattaIntent`) all hang off the regatta, while bookmarks, sailing events, and crew rosters hang off the per-day `Event`s. When in doubt: schedule data → `Event`; descriptive data → `Regatta`.

## Invariants

- **Datetime columns (`start`, `end`) use `UtcDateTime`** per `feedback_naive_datetime_convention`. Recently migrated from naked `DateTime` (commit `5a7ff17`). Note the regatta-rules doc still describes them as "naive local datetimes" — that doc describes the wire format the importer sends, not the column storage type. The column normalizes naive-as-UTC on the way in.
- **`slug` is globally unique when non-null** and is auto-generated from `name` via `_generate_slug` + `_ensure_unique_slug` in `routers/regattas.py`. Renaming a regatta re-slugs it. Bundle imports use a different slug shape (`{slug}-r{idx:02d}`) — see `scripts/season_bundle/upsert.py`.
- **Naming follows `docs/regatta/rules.md`.** Drop host abbreviations on distinctive names; lead with abbreviation only on generic series; use `#N` suffixes (no day-of-week); never smuggle handicap/qualifier tags into `name`.
- **`course_type` is a fixed lowercase vocabulary**: `buoy`, `windward/leeward`, `navigation`, `distance`, `government marks`, `fixed`. The UI icon keys off the exact lowercase string. Pursuit is a qualifier, not a course type.
- **`qualifier` is a JSON list of single-letter codes**: `Q`, `P`, `SH`, `O`, `J`, `S`, `W`, `H`. The MBSA calendar is authoritative — do not infer from race format. `Q` and `P` are mutually exclusive. Multiple codes stack.
- **`scoring_system` is the rating/handicap system, NOT scoring rules.** Valid values: `PHRF`, `ORR-Ez`, `IRC`, `ORC`, `One-Design`, `Portsmouth`. It is a list — a regatta can carry multiple ratings simultaneously. `"Low Point (RRS App. A)"` text belongs in `description`.
- **`__init__` always sets `type="Regatta"`** on the polymorphic `BaseModel`. Don't override.
- **OA mutation is double-gated**: `_require_manager` (role gate) plus `_require_regatta_org_scope` (the regatta's existing OAs must intersect the caller's UserRole scope) plus `_require_oa_scope` (the *new* OA set must also be administrable). Without all three, an `event_manager` from one club could hijack another club's regatta (commit `058aa8c`).
- **Multi-day regattas are NOT a series.** Use one `Regatta` with `start`, `end`, `max_races: N`. Series are for repeating week-after-week schedules.

## Gotchas

- **The model carries two parallel field generations.** Lines 12–22 are the canonical post-redesign columns. Lines 24–36 are legacy columns kept for SQLite compat with data migrated. **In practice, several of the "legacy" columns are still actively read and written** (`course_type`, `qualifier`, `links`, `max_races` all appear in current router and importer flows). Don't blindly remove them — the comment is aspirational.
- **`oa_uuid` (singular, on the model) is superseded by `OrganizationRegatta` (many-to-many).** `series.py:258` still copies `s.oa_uuid → regatta.oa_uuid` when generating races, but actual permission checks go through `OrganizationRegatta` via `get_owning_org_ids_for_regatta`. If you read OA from `regatta.oa_uuid`, you'll miss multi-host events.
- **`Regatta.series_uuid` is a UUID string, not a FK.** Series deletion does not cascade. Orphaned regattas pointing at deleted series are possible.
- **Two race-creation paths exist.** `POST /api/series/{id}/generate-races` (manual UI fallback, slugs by name) and `scripts/season_bundle/upsert.py` (bundle importer, slugs by index). They do not reconcile. Mixing paths produces duplicate or shadowed regattas.
- **Pursuit confusion bit twice.** Originally modeled as `course_type: "pursuit"`; corrected to `qualifier: ["P"]` during the Apr 8 calendar cleanup. Importers and LLM extractors still occasionally regress — verify on import.
- **Duplicate-check is fuzzy substring.** `POST /api/regattas/check-duplicates` matches if either name contains the other (when both >10 chars). Intentional for series races but can false-positive across years.
- **Match-roster delegates to `services/match_counts.py`.** That service depends on `Event.regatta_id`, not on `Regatta.id` directly — orphan `Regatta` rows with no `Event` show zero counts silently.
- **Re-slug on rename can break external links.** `links.nor_url`, `links.registration_url` are independent — the slug change doesn't cascade. Old slug returns 404; no redirect is issued.

## Cross-cutting concerns

- **`Event` (`category="regatta"`, `regatta_id` FK)** is the per-day calendar surface. One `Regatta` → N `Event`s. All bookmarks, sailing events, crew rosters, and per-day toggles live on the `Event`/`SailingEvent`, never on the `Regatta`.
- **`Series`** groups regattas via `Regatta.series_uuid`. Series-level fields are *templates* copied onto child regattas at generation time — later edits to the Series do not propagate. Series and Regatta share OA conventions.
- **`OrganizationRegatta`** is the M2M join for organizing authorities. The legacy `oa_uuid` column on `Regatta` itself is no longer authoritative; permission gates always go through this join via `services.organizing_authorities`.
- **`EventCrew`** rows live on `SailingEvent`s of the regatta's child events. Match-roster aggregates these to compute `boats_looking` and `crew_available`.
- **`EventDiscount` / `OrganizationEvent`** apply at the `Event` (per-day) layer, not at `Regatta`.
- **`PersonRegatta` / `RegattaIntent` / `RegattaDocument`** hang directly off the regatta UUID. Document uploads and per-person interest tracking are regatta-scoped.
- **Auth**: read endpoints are public; write endpoints require `event_manager | org_admin | system_admin` *and* org-scope match for the regatta's OAs (Tier C enforcement, commit `058aa8c`).
- **Memory feedback applies**: `feedback_naive_datetime_convention` (UtcDateTime), `feedback_timezone_helpers_mandatory` (frontend), `feedback_deploy_no_data_mutation` (re-deploys schema-only).

## External consumers

- **Concorda iOS app (Expo)** consumes `/api/regattas` for the calendar list and `/api/regattas/{id}` for detail. Field renames break it — coordinate before adding required fields.
- **Bulk season importer** (`scripts/season_bundle/upsert.py`) is the only authoritative source for series-derived regattas. It bypasses `_generate_slug` in favor of indexed slugs.
- **`docs/regatta/rules.md`** is consumed by the LLM-assisted regatta-entry workflow — naming/qualifier/course-type rules are baked into prompts. Updating the model's vocabulary requires updating that doc.
- **Calendar `.ics` feed** sources from `Event` rows but joins back to `Regatta` for description and links. Slug renames affect the URLs embedded in feed entries.

## Open questions

- **When do the legacy columns drop?** The two-generation split has lasted across multiple schema redesigns. Either reclassify them as canonical or migrate to JSON `additional_data`/`course` blobs.
- **Should `description` and `location` move to JSON?** Both have `# future: JSON` comments. No migration scheduled.
- **Series→Regatta propagation.** Series-level edits do not cascade to already-generated child regattas. Should they? Currently silent divergence.
- **Series-orphan cleanup.** Deleting a Series leaves regattas with dangling `series_uuid`. No FK constraint, no cleanup pass.
- **Slug redirects on rename.** No 301 / alias mapping; old links 404.
- **`H` (Hingham Bay) qualifier has no UI badge** per `docs/regatta/rules.md`. Either ship the badge or drop the code.
