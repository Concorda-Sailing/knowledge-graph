---
node_id: concorda-api::schemas/event.py::EventRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fb11d43066d01e34547278cd5edfc4ea2225b63d04d0318dd611a3341f1874ff
status: current
---

# EventRead

## Purpose

Backend Pydantic read schema for `Event` — the response shape returned by every event endpoint (custom-create, list, detail, calendar, image upload/delete). Carries `id`, `name`, `date`/`end_date`, `category`, `regatta_id`, `source_event_id`, `organizing_authorities[]`, plus the routine fields (`location`, `price`, `description`, `members_only`, `region`, `slug`, `image_url`, `comment`, `owner_id`). Subclassed by `EventReadWithRegatta`, which extends with `regatta_type`, `notice_of_race_url`, `sailing_instructions_url` for surfaces that show regatta detail. 7 dependents.

This is the "bare event" envelope, distinct from the richer `ScheduleItem` shape that `_build_schedule_item_for_event` produces. `EventRead` is what `eventsApi.get(id)` returns; `ScheduleItem` is what `eventsApi.getDetail(id)` and `eventsApi.mySchedule()` return. Don't conflate.

## Invariants

- **`from_attributes = True`** — built from a SQLAlchemy `Event` row via `EventRead.model_validate(event)`. Field names mirror the model's column names exactly; renaming a column is a breaking schema change.
- **`category` defaults to `"social"`**, matches the model default. Valid values are `social`, `regatta`, `personal` (`routers/events.py:29` `VALID_CATEGORIES`). Adding a fourth requires touching both the model and this schema.
- **`members_only` defaults to `False`**; `category` defaults to `"social"`. Most other fields are `Optional`. The required core is `id`, `type`, `created`, `modified`, `name`, `date`.
- **All datetimes are `UtcDateTime`-sourced** per `feedback_naive_datetime_convention` — they round-trip as aware UTC. Frontend must use `lib/datetime.ts` + org TZ for display, never raw `Date` methods.
- **`organizing_authorities`** is the eager-serialized list of `OrganizingAuthoritySummary` (id/name/slug/abbreviation/region). Empty list, never null. Populated by the relationship on `Event`.

## Gotchas

- **`EventReadWithRegatta` re-declares `regatta_id`** (already on the parent). Cosmetic, but if you change the parent's type you must change the child too or Pydantic picks the child's annotation.
- **`source_event_id` is on `EventRead` but not on `EventCreate`/`EventUpdate`** — it's a server-set field for personal-bookmark chaining. Frontend can read but never write it.
- **`sailing_event` is not on this schema** despite the user-facing framing. Sailing event details come back via `/api/events/{id}/sailing-event` returning `SailingEventRead` (a sibling schema in `routers/events.py`, not `schemas/event.py`).
- **`type` is a string field** at position 2 — it's the SQLAlchemy polymorphic discriminator, not the `category`. Don't switch UI on `type`; use `category`.
- **Personal events leak risk**: this schema doesn't filter `category == "personal"`. Listing endpoints must filter at the query layer (see Event model dossier — `routers/events.py:111, 134, 730, 845`). Adding a new endpoint that returns `list[EventRead]` without that filter leaks personal events.

## Cross-cutting concerns

- **`rule::schedule::canonical_listing`**: `EventRead` is *not* the schedule row shape. Schedule surfaces use the richer `ScheduleItem` from `_build_schedule_item_for_event`. Use `EventRead` for the bare event envelope (CRUD, slug lookup, public listings); use `ScheduleItem` for "things on my plate."
- **External consumers**: Concorda iOS app and `concorda-web` both consume this shape. Field renames here propagate to both — coordinate before adding required fields or removing optional ones.
- **Calendar feed (.ics)**: serializes from `Event` rows directly, not from this schema, but field semantics must stay aligned.

## External consumers

Concorda iOS Expo app consumes the same shape via its own `Event` typed reads. No webhooks; no scheduled jobs deserialize this shape.

## Open questions

- **`start`/`end` aren't on this schema yet** even though the model has them (transition shim — see Event dossier). When the legacy `date`/`end_date` columns get dropped, this schema flips. Plan the bump.
- **Should `EventReadWithRegatta` collapse into `EventRead`** with always-optional regatta fields? The split exists so non-regatta endpoints don't promise URLs they'll never have, but it doubles the schema surface.
