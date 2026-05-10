---
node_id: concorda-api::schemas/sailing_resume.py::SailingResumeRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b41f62147ef4fe4526e12670597cfc00435ef2960f9126aee4ff30bc556ed20
status: llm_drafted
---

# SailingResumeRead

## Purpose

`SailingResumeRead` is the wire-format Pydantic schema for reading a user's sailing resume — race history, certifications, availability, race areas, `positions_preferred`, the `*_ids` filter lists, and the US/World Sailing credentials. It is the response shape for `GET /api/profile/sailing-resume` (the user's own resume) and the building block underneath `CrewfinderProfileDetail` for `GET /api/crewfinder/{resume_id}` (peer detail). It is also the response shape for `POST /api/crewfinder` and `PUT /api/crewfinder/{id}` and `PUT /api/profile/sailing-resume` upserts. When deciding where to add a "what shape does the frontend see for a sailing resume" field, this is the right schema. It mirrors `SailingResume` (the model) field-for-field with `from_attributes = True`, so any column added on the model needs to be added here too or it silently disappears from the API response.

## Invariants

- **Field set is a strict superset of the editable fields plus `id`/`type`/`created`/`modified`.** `SailingResumeCreate` and `SailingResumeRead` are kept structurally parallel — every column on the model that is user-editable appears in both. Drift between them is a frequent source of "the field saved but doesn't come back" bugs.
- **`type` is always the string `"SailingResume"`.** Set by the model's `__init__`; the schema does not validate or default it. Treat as opaque for the frontend.
- **`achievements` is structured (`list[Achievement]`), not a list of strings.** The `_achievements_legacy` validator coerces legacy string-list rows into `{award: str}` dicts on read so old DB rows don't 500. Removing the validator will break any pre-`8b9722a` resume that still has unmigrated string achievements.
- **`availability` is typed as `Optional[dict]` here, not the structured `Availability` model.** This is intentional — reads accept arbitrary JSON-shaped availability blobs (including legacy `weekends`/`evening_races`/`specific_dates` keys) without 500ing on schema mismatch. Don't tighten this without a data audit.
- **`from_attributes = True` is load-bearing.** Routers return ORM `SailingResume` instances directly; Pydantic reads attributes off them. Removing this breaks every consumer.

## Gotchas

- **No `opt_in` flag on this schema.** Crewfinder visibility is gated by `Person.preferences["crewfinder"]["opt_in"]`, *not* by anything in the resume. A resume row coming back from this schema does not mean the user is browsable — see the `SailingResume` model dossier and `rule::crew_visibility::peer_pii_resume_gated`.
- **Allowlist drift on writes.** The two upsert paths maintain hand-written `SAILING_RESUME_ALLOWED_FIELDS` sets (`routers/profile.py:401`, `routers/crewfinder.py:464`). Adding a field here without updating both allowlists means writes silently drop the field while reads return the column unchanged. Recent additions (`f311f7a` for `us_sailing_number`/`world_sailing_id`/`world_sailing_group`, `d7c718e` for `preferred_oa_ids`, `8b9722a` for structured `achievements`) all required four-file changes — model + schema + both allowlists.
- **`CrewfinderProfile` and `CrewfinderProfileDetail` are not subclasses of this schema.** They independently re-list a subset of fields plus joined Person data (name, email, phone, banner). Adding a field to `SailingResumeRead` does *not* automatically expose it on the crewfinder browse/detail surfaces — that requires editing the `CrewfinderProfile*` schemas and the `_build_crewfinder_profile` helper.
- **`person_id` is a string, not embedded `Person`.** Consumers that need first/last name must call a separate endpoint or use the `CrewfinderProfileDetail` shape, which is not what `GET /api/profile/sailing-resume` returns.
- **The `*_ids` JSON columns are reflected here as `list[str]`** — the M2M-loaded `boats_sailed`/`excluded_boats`/`no_contact_boats` relationships on the model are *not* exposed through this schema. Consumers that need full boat objects join client-side or use a different endpoint.

## Cross-cutting concerns

- **Auth**: every endpoint returning this shape is behind `require_auth`. `GET /api/profile/sailing-resume` is scoped to `current_user.id`; the crewfinder endpoints allow reading any resume by id but are gated by the crewfinder opt-in predicate before the response is built.
- **WebSocket**: the model's `SAILING_RESUME_UPDATED` / `SAILING_RESUME_DELETED` events carry resume payloads in this shape. Frontend subscribers parse against this schema's TypeScript mirror.
- **Crew-visibility rule (`rule::crew_visibility::peer_pii_resume_gated`)**: this schema is the wire format the rule governs *exposure* of. PII fields (notes, about_me, certifications, achievements) are surfaced on `CrewfinderProfileDetail` only when the target person's `crewfinder.opt_in` is true.
- **Profile-completion scoring** on the web client reads `positions_preferred` and `availability` presence off this shape to compute the dashboard "needs setup" badge — field renames here zero out completion silently.

## External consumers

- **Concorda iOS app** consumes `GET /api/profile/sailing-resume` and expects this exact field set; renames need app-side coordination.
- **Web frontend** mirrors this schema as the `SailingResume` TypeScript interface in `concorda-web/src/lib/api.ts`; 9 web call sites consume it (see the `profileApi.getSailingResume` dossier).
- No scheduled jobs, webhooks, or third-party integrations consume this schema directly.

## Open questions

- **Should `availability` be tightened to the `Availability` model on reads?** It's `dict` to tolerate legacy rows, but new writes go through the typed `Availability` and validate. A backfill + tightening would let the frontend trust the shape.
- **Should `CrewfinderProfileDetail` inherit from `SailingResumeRead` instead of duplicating fields?** The current parallel-list design has been the source of "added field doesn't show up on crewfinder detail" bugs. Inheritance would couple them — possibly the right thing.
