---
node_id: concorda-api::schemas/boat_resume.py::BoatResumeRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a2819d0cce90021bc1836072aaef62d87f39bb8ce48141f1bf49888311dac861
status: llm_drafted
---

# BoatResumeRead

## Purpose

`BoatResumeRead` is the wire shape for "owner reading their own boat's recruitment bio." Returned by `GET /api/profile/boats/{id}/resume` (the dominant consumer), `GET /api/profile/boat-resumes` (the per-person list across owned boats), and as the `200` body of `PUT /api/profile/boats/{id}/resume` (the upsert). Mirrors the `BoatResume` model 1:1 plus the row-level `id`/`type`/`created`/`modified`. This is the **owner-side** view — peer/public reads of a boat's recruitment profile go through `BoatFinderProfile` / `BoatFinderProfileDetail` (same module), which strip drinking posture for non-detail and surface owner identity. Future Claude: when adding a column to `BoatResume`, this is one of the three Pydantic surfaces that must be updated; when surfacing a *new* field publicly, also add it to `BoatFinderProfile*`.

## Invariants

- `from_attributes = True` — populated directly from the `BoatResume` ORM row; field names must match the model exactly.
- `id`, `type`, `created`, `modified`, `boat_id` are non-optional. `type` is always the string `"BoatResume"` (hardcoded in the model `__init__`); clients can switch on it when the same envelope carries multiple resume kinds.
- `looking_for_junior_crew: bool = False` and `published: bool = False` are non-Optional with defaults — the wire will always carry a concrete bool, never `null`. `BoatResumeCreate`/`Update` keep them Optional; Read does not. Don't "fix" this asymmetry without checking iOS — it relies on the bool being present.
- Field set must stay in lockstep with `BoatResume` model columns AND with `BOAT_RESUME_ALLOWED_FIELDS` in `routers/profile.py:1030`. Drift between any of the three is the recurring failure mode for this module.
- `positions` and `race_areas` are `list[str] | None`; `availability` is a free-form `dict | None`. No server-side schema on availability — clients define the shape.

## Gotchas

- **Drift hazard across three schemas + model + allowlist.** Adding `boat_program_url` means: column on `BoatResume`, field on `BoatResumeCreate`, on `BoatResumeUpdate`, on `BoatResumeRead`, on `BoatFinderProfile*` if peer-visible, and on `BOAT_RESUME_ALLOWED_FIELDS`. Missing any one silently drops the field from a code path. See the `BoatResume` model dossier for the full list.
- **`accepting_crew` here is the boat-level captain bio, not the per-race toggle.** Same trap that bit commit `6c9b5f3` — UI consuming `BoatResumeRead.accepting_crew` must not be wired to the regatta-calendar "Accepting Crew" badge; that badge reads `SailingEvent.accept_crew_requests`. Read the `BoatResume` model dossier before touching this field.
- **`published` is exposed here but the endpoint ignores it.** The owner sees their unpublished draft via this schema; `published` is the boatfinder visibility gate, enforced on the boatfinder surface, not on `/profile/boats/{id}/resume`. Don't copy-paste this response into a peer-facing view without re-filtering.
- **404 envelope is not this schema.** `GET /api/profile/boats/{id}/resume` returns 404 for both "boat not found" and "resume row not yet created"; first-time owners see no `BoatResumeRead` at all. The 5 web consumers wrap in try/catch — see the `profileApi.getBoatResume` dossier.
- **No `Boat` denormalization.** Unlike `BoatFinderProfile`, this schema does not carry `boat_name`, `sail_number`, `picture_url`, or owner identity. Owner-side UIs that need those join client-side against `profileApi.getBoats()`.

## Cross-cutting concerns

- **Auth**: only emitted from owner-gated endpoints (`require_auth` + active `BoatCrew.role=='owner'` via `_owner_query`). Co-owners with `status='pending'` cannot trigger emission. Never returned by the public boatfinder.
- **WebSocket**: this schema is the payload of `BOAT_RESUME_UPDATED` (`boat_resume.updated`) broadcasts from the upsert at `routers/profile.py:1051`. Subscribers expecting that event must accept this exact shape; renaming a field breaks live-refresh on every consumer simultaneously.
- **iOS coupling**: the Concorda iOS boat-resume editor decodes this shape directly. Server-side field renames need a coordinated app release; additive optional fields are safe.
- **No audit trail beyond `modified`.** No `published_at`, no who-edited-last. If audit lands on `BoatResume`, decide whether it surfaces here or stays internal.

## External consumers

- **Concorda iOS app** decodes `BoatResumeRead` in its boat-resume editor screen.
- **Web boat-resume editor surfaces** — dashboard, setup page, `boat-inline`, `boat-owner-view`, `boat-setup-wizard` (5 sites, all via `profileApi.getBoatResume`).
- No scheduled jobs, no webhooks, no third-party integrations.

## Open questions

- Should `published` flip to a `published_at: datetime | None` on the wire to match a future model-side change? Tracked on the `BoatResume` model open questions; this schema is the visible surface.
- Should `BoatResumeRead` embed minimal `Boat` identity (name, sail_number) to spare consumers a second call? The five current consumers all already have the boat loaded, so probably not — but the iOS editor would benefit.
- Should the 404-on-missing-row pattern be replaced with `200 { resume: null }`, and if so, does this schema become `BoatResumeRead | None` at the OpenAPI layer? Same open question as on `SailingResumeRead`.
