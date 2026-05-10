---
node_id: concorda-api::models/sailing_event.py::SailingEvent
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b8a9d77d2afb4e2b2673f38f3687364e638abdc383d0a8f28889de5089ed422e
status: current
---

# SailingEvent

## Purpose

Backend SQLAlchemy model representing **one captain's plan for one boat at one event** — a race, delivery, training sail, or cruise. Where `Event` is "this regatta exists on the calendar," a `SailingEvent` row is "I, owner of *this* boat, am sailing it in that event, leaving the dock at *this* time, with *these* positions and *this* crew pool." The `(event_uuid, boat_uuid)` pair is the de-facto unique key — multiple captains each get their own SE on the same Event, so any lookup must scope by caller-owned boat (see `PUT /api/events/{0}/sailing-event` dossier — that scoping is load-bearing). Carries the logistics payload (`dock_time`, `departure_time`, `estimated_duration`, `departure_location`, `arrival_location`, `arrival_time`, `notes`), the per-race position snapshot (`positions_needed`), and the crew-recruitment knobs (`crew_pool_id`, `accept_crew_requests`, `crew_group_priority`, `boat_config_id`). Fans out to nine direct dependents — captain-side editors, schedule build, crew-suggest, crew-request inbox, my-schedule aggregator, regatta/series fan-out, profile crew rollup.

## Invariants

- **`event_uuid` is required and indexed; `boat_uuid` is nullable but indexed.** A boat-less SE is a transient state (created via the bulk regatta/series add paths before the captain picks a boat); the captain-facing upsert path 400s on first-time create without a `boat_uuid`. Don't relax the nullable on the column without auditing those bulk paths.
- **`positions_needed` is a snapshot of `Boat.positions` at SE-create time**, not a live reference. Shape is `[{name, filled_by_uuid}]`. Changes to `Boat.positions` do not propagate (cascade was attempted in `31aa70d`, reverted in `d54327b` — see Boat dossier). Treat per-SE `positions_needed` as authoritative for that race.
- **Datetimes go through `UtcDateTime`** (`5a7ff17`). Stored naive-as-UTC, round-tripped tz-aware. Never assign a tz-aware datetime that has been pre-converted to local — store UTC, render in org TZ at the edge.
- **`crew_pool_id` references a `CrewPool` whose `boat_uuid` matches this SE's `boat_uuid`** — enforced at the upsert handler, not at the DB level. Moving an SE to a different boat without re-pointing the pool is a corruption-shaped bug.
- **`crew_confirmed: bool`** is the captain's "roster locked" toggle; not a status enum. Distinct from per-row `EventCrew.status='confirmed'`.
- **`accept_crew_requests: bool` is per-SE** (`b67d359`), not per-boat — preserve on partial updates or the regattas-page "Accepting Crew" badge flickers off.
- **`__init__` injects `type="SailingEvent"`** on the BaseModel discriminator. Don't construct via `SailingEvent.__new__` or you'll get a row with `type=NULL` that won't round-trip.

## Gotchas

- **No DB-level uniqueness on `(event_uuid, boat_uuid)`.** The "one SE per (event, owner-boat)" contract is enforced only by the upsert handler's caller-scoped lookup; raw inserts or migrations could produce duplicates that the captain UI then renders ambiguously.
- **`boat_config_id` is persisted, not inferred** (`d61a069`). The crew-config dropdown previously shape-matched against `Boat.configurations` on each load and lost the user's selection across reloads. Read this column directly; do not re-derive from positions.
- **Calendar-email side effect lives upstream of this model** — `PUT /sailing-event` dispatches `logistics_set` / `logistics_updated` / `event_canceled` mails when `dock_time` transitions or any of `(dock_time, arrival_time, departure_time, departure_location, arrival_location, estimated_duration, notes)` changes alongside an existing dock (`b06df47`). **Adding a new logistics field here without also adding it to the handler's `_watched` snapshot is a silent failure.**
- **`crew_group_priority` is in the column list and the upsert schema but not currently surfaced in either web consumer** post-consolidated-crew-card — likely dead or partially wired. Don't repurpose without checking the priority-system code path.
- **`event_subtype` is a free `String(30)`** with comment-documented values (`race`, `delivery`, `training`, `cruise`, `other`). No enum, no CHECK. New values land freely; downstream code that switches on subtype must default safely.
- **`positions_needed` JSON shape is duck-typed.** Crew-suggest, crew-assign, and crew-position endpoints all read `[{name, filled_by_uuid}]`; adding fields is fine but renaming `name` or `filled_by_uuid` is a coordinated change across at least four routers.

## Cross-cutting concerns

- **Auth**: writes are caller-scoped via `BoatCrew(role='owner', status='active')` join, then `_require_boat_owner` on any `boat_uuid` change. Reads on `/my-schedule` and `/profile/crew` join through `BoatCrew` to surface co-owned boats' SEs (per `rule::schedule::canonical_listing`).
- **Schedule canonical listing**: SailingEvent rows are source #5 of `_build_schedule_item_for_event`'s five-source aggregation (co-owned boats' events). Any new schedule-shaped surface must route through that helper, not this model directly.
- **Email side effects**: `.ics` mails dispatched on logistics transitions to active roster (`invited`/`accepted`/`confirmed` only — pool candidates and declined skipped). Failures swallowed; not transactional with the SE write.
- **Calendar feed**: `/api/schedule/feed/{token}.ics` serializes SEs into iCalendar; `ics_sequence` on `EventCrew` (not here) is what invalidates Apple/Google calendar caches.
- **No websocket broadcast** on SE writes — clients re-fetch (schedule detail) or rely on parent-component reload (event-plan-panel).
- **Audit**: none. The `prev_values` diff is computed only to gate emails; nothing persists a logistics-change log.

## External consumers

- **Concorda iOS app** consumes `/my-schedule` and crew endpoints, which read SE rows through the schedule helper. Adding fields here is safe; renaming/removing requires coordinated app release.
- **Calendar subscribers** (Apple Calendar, Google Calendar via `.ics` feed) inherit SE logistics fields through ICS rendering.
- **Playwright test suite** (`concorda-test`) drives both the full-payload upsert and the bare-`{boat_uuid}` attach-boat shim path.

## Open questions

- **DB-level uniqueness on `(event_uuid, boat_uuid)`** — should this be a constraint, given the upsert handler is the only intended writer? Migration risk vs. corruption-prevention tradeoff.
- **`crew_group_priority` lifecycle** — alive, dead, or partially wired post-consolidated-crew-card? Audit before next crew-priority feature.
- **`event_subtype` controlled vocabulary** — same shape question as `Boat.boat_class`; would help with subtype-aware schedule rendering, not pressing.
- **Boat-less SE rows** — bulk regatta/series add paths create them; should they have a TTL or visibility filter so they don't leak into "no boat assigned" schedule slots indefinitely?
