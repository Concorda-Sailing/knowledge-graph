---
node_id: concorda-api::models/boat_resume.py::BoatResume
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 56338e7e201845e16f30a2282cb80ea07f0834b0106d26f74485985a66991778
status: current
---

# BoatResume

## Purpose

`BoatResume` is the per-boat recruitment profile — the boat owner's side of the matchmaking equation. Where `SailingResume` is "what kind of crew I want to be," `BoatResume` is "what kind of crew I'm looking for and how to find them": the boat's free-text bio (`about`), program ethos (Competitive/Casual/Beginner), positions the captain is recruiting for, race areas the boat sails, the captain's drinking/junior-crew posture, and a top-level `published` flag that gates inclusion in the boat finder. One row per boat. The boat owner edits it from `Profile -> My Boats -> Resume`; the rest of the membership reads it through the boat finder. When deciding where to put a "what I'm looking for as a captain" field, this is the right model. When the field is per-race rather than per-boat (e.g., this Saturday's accept-crew toggle), it belongs on `SailingEvent`, not here — see the Gotchas.

## Invariants

- **One resume per boat by convention.** All upsert and read paths key on `boat_id` and use `.first()`; nothing in the schema enforces uniqueness. The upsert at `routers/profile.py:1020` does query-then-create-or-update — concurrent writers could race, but in practice only the boat owner writes.
- **`boat_id` is a string FK by convention only.** `String(36)` matches the UUID PK shape; no `ForeignKey` constraint, just an index. Lookup-by-boat is the dominant access pattern.
- **`type` discriminator is `"BoatResume"`.** `__init__` hardcodes `super().__init__(type="BoatResume", ...)`. Do not pass `type=` from callers.
- **`published == True` is the boat finder's visibility gate.** Every boatfinder query filters `BoatResume.published == True` — list, search, detail, contact, apply (`routers/boatfinder.py:87,131,176,229,292`) and the crewfinder split-view (`routers/crewfinder.py:82,183`). An unpublished resume is invisible to non-owners. Owners read their own resume through `/api/profile/boats/{boat_id}/resume`, which does not check `published`.
- **Edit authorization = active ownership in `BoatCrew`.** All four mutating profile endpoints call `_owner_query(db, boat_id, person_id)` which requires `BoatCrew.role == "owner"` AND `BoatCrew.status == "active"`. Crew-with-status-pending owners cannot edit. There is no per-resume ACL beyond boat ownership.
- **Free-text fields are length-bounded** (`String(2000)` for `about`, `String(20)` for `ethos` and `accepting_crew`, `String(30)` for `drinking`). The short String() lengths are tight — don't add a fourth ethos value like "Performance Cruising" without widening the column.
- **`positions`, `race_areas`, `availability` are JSON columns.** `positions` and `race_areas` are list-of-strings; `availability` is a free-form dict. Filters in boatfinder do Python-side `in` checks (`routers/boatfinder.py:92,95,139`), not SQL JSON queries — fine at current scale, won't be at 10k boats.

## Gotchas

- **`accepting_crew` is the boat-level captain bio, NOT the per-race toggle.** Commit `6c9b5f3` (2026-05-06) fixed a regatta-calendar bug where the Accepting-Crew badge on the regattas page was reading `BoatResume.accepting_crew` ("Yes"/"Occasionally"/"No") and ignoring `SailingEvent.accept_crew_requests` (the per-event boolean the skipper actually toggles per race). Rule: `BoatResume.accepting_crew` drives the **boat finder** and the static **boat resume view**; `SailingEvent.accept_crew_requests` drives the **per-race** "looking for crew" badge on the regatta calendar. Don't conflate them.
- **No DB-level dual storage like `SailingResume`.** Unlike `SailingResume` (which has the `*_ids` JSON / M2M junction split for boat lists), `BoatResume`'s JSON columns (`positions`, `race_areas`, `availability`) have no shadow junction tables. There's nothing to keep in sync — but also nothing to migrate to if these grow into normalized lookups.
- **Schema/model drift risk on `BOAT_RESUME_ALLOWED_FIELDS`.** The upsert maintains a hand-written allowlist (`routers/profile.py:1030`). Any new column on the model must be added here AND to `schemas/boat_resume.py` (three classes: Create, Update, Read) AND to `BoatFinderProfile` / `BoatFinderProfileDetail` if it should surface to non-owners. Migrations live separately under `migrations/`. Same field-allowlist hazard as `SailingResume`.
- **Boatfinder filters short-circuit on `None` JSON columns.** The pattern `if race_area and br.race_areas: ... elif race_area and not br.race_areas: continue` means a boat with `race_areas IS NULL` is excluded from any filtered search but visible in unfiltered listing. Same for `positions`. Easy to misread when adding a new filter.
- **`/api/profile/boats/{boat_id}/resume` 404s when no resume exists.** The web/iOS UX for "edit boat resume" must handle the 404 as "create new" not "error." The `PUT` handles upsert correctly; the `GET` does not.

## Cross-cutting concerns

- **Auth (read paths)**: public boat finder list (`GET /api/boatfinder`) is unauthenticated and returns only `published=True` resumes — anyone on the internet can browse these. The authenticated search/detail endpoints additionally require `boatfinder.view` permission. Owner-side reads (`/api/profile/boats/{id}/resume`, `/api/profile/boat-resumes`) require `require_auth` plus `_owner_query` ownership.
- **Auth (contact/apply)**: `boatfinder.contact` perm gates the email-proxy paths. Self-contact / self-apply is rejected. Rate-limited at 10/hour per sender via in-memory `_contact_rate_limit` dict in `routers/boatfinder.py:22` — same single-worker-only limitation noted in `feedback_rate_limiter_single_worker`.
- **Boat ownership coupling**: this model has no FK to `Boat` or to any owner Person. The boatfinder resolves the owner at read time via `_get_boat_owner(boat_id, db)` which picks the *first* `BoatCrew.role=='owner', status=='active'` row. Co-owned boats display only one owner's name on the boat finder card. If all owners are deactivated, the boat is silently dropped from the finder via the try/except.
- **Boatfinder ↔ SailingResume cross-filtering**: the authenticated boat search excludes boats listed in the *viewer's* `SailingResume.excluded_boat_ids` (boatfinder.py:126-129,150). So crew-side preference lists feed back into boat-side discovery. Removing or renaming `excluded_boat_ids` requires updating this surface.
- **Crewfinder split view**: `GET /api/crewfinder/search` returns both `crew_profiles` and `boat_profiles` and uses `BoatResume.published` as the gate for the boats list (`routers/crewfinder.py:183`). The "can_see_boats" predicate is "viewer has opted into crewfinder," not "viewer is published" — different from the symmetric crew-side gate.
- **WebSocket broadcasts**: `BOAT_RESUME_UPDATED` (`boat_resume.updated`) and `BOAT_RESUME_DELETED` (`boat_resume.deleted`) fire from the upsert and delete paths in `profile.py:1051,1090`. No broadcast from any boatfinder action — only the owner-side mutations notify subscribers.
- **No connection to `BoatCrew` rows.** `BoatCrew` is the active-roster table (owner/crew/prospective/declined). `BoatResume` is the captain's recruitment bio. The boatfinder *apply* endpoint creates a `BoatCrew(role="prospective")` row on apply (boatfinder.py:344-352), but the `BoatResume` itself never references `BoatCrew` and `BoatCrew` never references `BoatResume`.

## External consumers

- **Concorda iOS app** edits `BoatResume` via `GET/PUT/DELETE /api/profile/boats/{id}/resume` (boat-resume editor screen).
- **Web boatfinder surface** (public + members) reads via `/api/boatfinder*`.
- **Web crewfinder split view** consumes the published boat list embedded in `/api/crewfinder/search`.
- **Email proxy templates** (`send_crewfinder_contact_email`, `send_crew_application_email`) cite the boat's name and link the recipient to the sender's published boat finder card if the sender owns a published boat.
- No known scheduled jobs, no webhooks, no third-party integrations.

## Open questions

- **Should `published` be replaced with a `published_at: datetime | None` audit field?** The current boolean loses information about when a boat first went public, which is useful for finder-staleness display.
- **Should a UNIQUE constraint be added on `boat_id`?** Application logic enforces one-resume-per-boat; a UNIQUE index would make it load-bearing.
- **Is the regatta calendar's separation between `BoatResume.accepting_crew` (boat-level) and `SailingEvent.accept_crew_requests` (per-race) the right long-term model?** Commit `6c9b5f3` had to rebuild this; the boundary works but is subtle, and a future "is this captain looking for help right now?" UI will need to compose both signals.
- **Should boat-finder filtering move to SQL-JSON queries (`json_each`)?** Current Python-side filtering is fine at current scale; will not be at 10k boats. Same question lives on `SailingResume.race_areas` / `positions_preferred`.
