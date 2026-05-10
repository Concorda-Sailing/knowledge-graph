---
node_id: concorda-api::models/person_event.py::PersonEvent
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7c77ece54512917b5bab47e0bc1a0219b4170988083c0e8f4d90c9d62b335de6
status: current
---

# PersonEvent

## Purpose

Backend SQLAlchemy model for the (person, event) bookmark — the "I added this regatta to my schedule" row. Concretely a five-column join row (`person_uuid`, `event_uuid`, `relationship`, `role`, `description` JSON) keyed by the BaseModel `id`. This is **source #2** of the five sources fed into `_build_schedule_item_for_event` per `rule::schedule::canonical_listing` (the others being personal Events, EventRegistrations, EventCrew, and co-owned SailingEvents). It is the row written by `POST /api/events/my-schedule/add-regattas` (see `eventsApi.addRegattas` dossier) and torn down by `DELETE /api/events/my-schedule/events/{id}` (see `eventsApi.removeScheduleEvent` dossier). Future Claude: this is the bookmark layer — not registration, not crew assignment. Its presence on its own says "this user wants this event on their schedule"; the optional `role` discriminates captain-mode (with a SailingEvent attached) from crew-mode (just a bookmark).

## Invariants

- **Uniqueness is by (person_uuid, event_uuid, relationship)**, enforced in application code (no DB unique constraint today). All five write/read sites in `routers/events.py` filter on `relationship == "schedule"` before insert; if a future caller skips that filter it will produce duplicate bookmarks.
- **`relationship` is currently always `"schedule"` in production code paths.** The column is sized `String(50)` and the framing left room for `"captain"` / `"social_attendee"` variants, but neither is written or queried anywhere in `concorda-api` today. The captain/crew distinction lives in **`role`**, not `relationship`.
- **`role` is `'captain' | 'crew' | None`** (commit `7e6ed14`). NULL means legacy or non-regatta bookmark; `match_counts` falls back to inferring captain from SailingEvent ownership when `role is None`.
- **`person_uuid` and `event_uuid` are indexed but not foreign keys** — both are bare `String(36)`. Dangling rows after Person/Event deletion are possible; cleanup is the deleter's job (see Gotchas).
- All five known callers go through `relationship="schedule"`; preserve that filter when adding a sixth.

## Gotchas

- **Captain-add upgrades, crew-add is a no-op when a row exists.** `addRegattas` checks for an existing PersonEvent and either updates `role` to `"captain"` (captain branch, events.py:751) or skips entirely (crew branch). There is no "downgrade captain → crew" path through normal endpoints; teardown-and-re-add is the only way back.
- **Removal cascades onto OTHER users' rows.** The co-owner branch of `_cleanup_sailing_event` (events.py:1041, 1151) deletes `PersonEvent` rows belonging to *other* boat owners and to crew members invited to the SailingEvent — not just the caller's row. A future maintainer treating PersonEvent as "owned by `person_uuid`" will be surprised by writes coming from someone else's delete request.
- **No FK / no cascade**: dropping an Event does not delete its PersonEvents. Cleanup scripts and the SailingEvent teardown path do this manually; the orphan-Event check at events.py:1041 only fires when SE deletion runs.
- **`role` was added 2026 in commit `7e6ed14` to fix `match_counts`** — historical rows (pre-redesign `ee82e42`) may have NULL role even for captain bookmarks. `match_counts` infers from SailingEvent ownership in that case; do not assume `role IS NOT NULL` post-migration.
- **`description` JSON is a freeform escape hatch** — no schema, not consulted by any reader I found. Treat as opaque.

## Cross-cutting concerns

- **Schedule rule (`rule::schedule::canonical_listing`)**: this model is source #2 of `_build_schedule_item_for_event`. Any new query against `person_events` that returns schedule-shaped data should route through that helper, not build its own row shape.
- **Calendar feed**: `routers/calendar.py:161` reads PersonEvent (`relationship == 'schedule'`) to assemble the user's `.ics` subscription — same scope as `my-schedule`. Schema changes that affect what shows on the schedule must also be verified against the ICS feed.
- **match_counts service** (`services/match_counts.py:93, 227, 351`) reads PersonEvent to compute "captains in this race / crew bookmarked / co-owner exclusion." `role` semantics must stay `'captain' | 'crew' | None` or that service silently miscounts.
- **Email side effects** are upstream (in `removeScheduleEvent`), not on this model. Direct PersonEvent CRUD does not emit websocket, audit, or email events today.
- **Auth**: indirectly gated — every writer is behind `require_auth` and writes only `current_user.id`. There is no admin override surface that writes PersonEvent on someone else's behalf; cross-user writes only happen via the cascade described above.

## External consumers

None known. Internal only: `routers/events.py` (5 sites), `routers/calendar.py` (1 read for ICS), `services/match_counts.py` (3 reads), and three test files. The Concorda iOS app sees PersonEvent contents only via the `my-schedule` aggregator, never directly. No webhook, scheduled job, or external integration touches this table.

## Open questions

- **Should `relationship` get a DB-level CHECK / enum** now that `"schedule"` is the only live value? Or commit to the framing (`captain` / `social_attendee` as parallel relationship values) and migrate `role` semantics into `relationship`? Currently there are two overlapping discriminators (`relationship` and `role`) where one would do.
- **Should (person_uuid, event_uuid, relationship) be a DB UNIQUE**? Application-level dedup has held so far but a sixth writer that forgets the existence check would silently double-bookmark.
- **Cascade on Event delete** — formalize as FK with ON DELETE CASCADE, or accept the current "deleter cleans up" contract? The `source_event_id` orphan note in the Event dossier hints at the same gap from the other side.
