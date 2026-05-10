---
node_id: concorda-api::models/sailing_resume.py::SailingResume
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d0983df0e2995d5a6cbd8091710272a8cd33b4f20783d01cb6757739326ef613
status: current
---

# SailingResume

## Purpose

`SailingResume` is the per-person record of "what kind of sailing I do, what I want to be invited to, and what I want kept off-limits." It is the canonical home for crew-side preferences (positions, race areas, experience level, certifications, US/World Sailing IDs) and for crew-side filters that drive the boatfinder (`excluded_boat_ids`, `no_contact_boat_ids`, `preferred_oa_ids`). One row per person; the existence of a row alone does not mean the person is browsable in the crewfinder — that is gated separately by `Person.preferences["crewfinder"]["opt_in"]`. When deciding where to put a new "what I want as a crew candidate" field, this is the right model. When deciding where to put a "what I'm looking for as a boat owner" field, prefer `BoatResume`.

## Invariants

- **One resume per person.** Both writers (`PUT /api/profile/sailing-resume` upsert at `routers/profile.py:384`, `POST /api/crewfinder` at `routers/crewfinder.py:431`) check for an existing row keyed by `person_id` before inserting, and the `POST` endpoint 400s on collision. There is no DB UNIQUE constraint enforcing this — relying on application logic.
- **`person_id` is a string FK by convention only.** `String(36)` matches the UUID PK shape but no `ForeignKey` constraint is declared on the column itself. Keep it indexed; lookup-by-person is the dominant access pattern.
- **`type` discriminator is `"SailingResume"`.** The `__init__` hardcodes it via `super().__init__(type="SailingResume", ...)`. `BaseModel` uses `type` as a polymorphic discriminator — do not pass `type=` from callers.
- **The `*_ids` JSON columns and the M2M relationships represent the same data.** `boats_sailed_ids` (JSON list) coexists with `boats_sailed` (M2M via `sailing_resume_boats`); same for `excluded_boat_ids` / `excluded_boats` and `no_contact_boat_ids` / `no_contact_boats`. Migration `006_junction_tables.py` populated the junction tables from the JSON lists. Both are still read in places. Treat the JSON columns as the source for upsert payloads (the upsert handlers write the `*_ids` lists, not the M2M relationships); the M2M relationships are for selectin-loaded reads.
- **All free-text fields are length-bounded** (`String(2000)` for `notes`, `about_me`, `notable_experience`; `String(500)` for `picture_url`). The text fields are user-supplied, so length validation belongs in the schema layer.
- **The three M2M relationships need `overlaps=` on each leg.** They all target `Boat`; SQLAlchemy emits warnings without the explicit overlaps. Do not remove these — they silence valid noise, not a real bug.

## Gotchas

- **"Has a resume row" ≠ "publishes a resume."** This is the most common LLM mistake on this surface. The crewfinder visibility predicate is `Person.preferences["crewfinder"]["opt_in"]`, not `SailingResume IS NOT NULL`. Code looking for "resume published" should call `services/visibility.py::has_published_resume(person)` and pass a `Person`, not a `SailingResume`. See `rule::crew_visibility::peer_pii_resume_gated`.
- **Field-allowlist drift.** Both upsert paths maintain a hand-written `SAILING_RESUME_ALLOWED_FIELDS` set (`routers/profile.py:401`, `routers/crewfinder.py:464`). Adding a column here without updating both allowlists silently drops the field from API writes. Recent additions (`preferred_oa_ids`, `us_sailing_number`, `world_sailing_id`, `world_sailing_group`) all required allowlist edits — easy to miss.
- **The model has accumulated columns in clusters.** `f311f7a` added the three `*_sailing_*` credential fields; `9519a7a` added `preferred_oa_ids`; migration `057_sailing_resume_sailing_credentials.py` and `add_sailing_resume_preferred_oa_ids.py` are the matching schema migrations. Migrations live on the api repo's migration runner — adding a column is a two-file change (model + migration) at minimum, three with the allowlists, four with the schema.
- **The boatfinder reads `excluded_boat_ids` from the JSON column directly** (`routers/boatfinder.py:129`), not via the M2M `excluded_boats` relationship. If you change one without the other (e.g., teach the upsert to write only the relationship), the filter silently stops excluding boats. Keep both in sync until the JSON columns are formally retired.
- **`broadcast_event(SAILING_RESUME_UPDATED, ...)` fires from the upsert path** (`profile.py:426`) and `SAILING_RESUME_DELETED` from delete (`profile.py:448`). Other surfaces (`POST /api/crewfinder`, `PUT /api/crewfinder/{id}`) do not broadcast. WebSocket subscribers will see updates from one path and not the other.

## Cross-cutting concerns

- **Auth**: every endpoint touching this model is behind `require_auth`. Profile-namespace endpoints scope by `current_user.id`; the `crewfinder/{resume_id}` endpoint allows reading any resume by id, gated only by login.
- **Crew-visibility rule (`rule::crew_visibility::peer_pii_resume_gated`)**: this model is the *named subject* of the rule but **not the signal that drives it**. The signal is `Person.preferences["crewfinder"]["opt_in"]`. The rule's `attribute::resume_published` is a synthesized boolean computed from the Person preference, not a column on this model. If a future redesign moves the opt-in flag onto `SailingResume` (e.g., a `published_at` column), update `services/visibility.py::has_published_resume` and the logigraph rule together.
- **Crewfinder search** filters by both `Person.preferences[...].opt_in` and `disabled_permissions` (excludes anyone with `crewfinder.view` disabled). The opt-in is the publish gate; the disabled-permissions check is the org-admin override.
- **Boatfinder** uses `excluded_boat_ids` to suppress boats from a person's results and `preferred_oa_ids` for ranking/filtering. These are *crew-side* filters expressed on the resume — boat-side equivalents live on `BoatResume`.
- **WebSocket broadcasts**: `SAILING_RESUME_UPDATED` / `SAILING_RESUME_DELETED` are emitted from the profile upsert/delete paths only. The Expo iOS app subscribes to these to refresh the resume editor without a manual reload.

## External consumers

- **Concorda iOS app** consumes `GET /api/profile/sailing-resume` and writes via `PUT`. Field renames here require app-side schema updates; coordinate before changing existing field names.
- **Crewfinder browse surface** (web + iOS) reads via `GET /api/crewfinder` and `GET /api/crewfinder/{resume_id}`.
- **Boatfinder** (web) reads the user's own resume to apply `excluded_boat_ids` filtering.
- No known scheduled jobs, no webhooks, no third-party integrations consume this model directly.

## Open questions

- **Should the `*_ids` JSON columns be retired in favor of the M2M relationships?** The dual representation has been a low-grade gotcha for a while. Migration `006` populated the junctions but did not drop the JSON columns. Retiring the JSON columns requires updating boatfinder, both upsert allowlists, and the schemas — non-trivial but bounded.
- **Should there be a DB-level UNIQUE constraint on `person_id`?** Application logic enforces one-resume-per-person; a UNIQUE index would make the invariant load-bearing rather than aspirational.
- **Should `picture_url` be a separate concept from `Person.picture_url`?** The crewfinder profile builder falls back from `resume.picture_url` to `person.picture_url` (`crewfinder.py:166`). Two sources, one display field — unclear which should be canonical.
