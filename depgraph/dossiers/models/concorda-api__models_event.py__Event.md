---
node_id: concorda-api::models/event.py::Event
node_kind: model
feature: events
last_reviewed: 2026-05-10
last_reviewed_against_hash: ff987f0c2fc9f71f1793195f1bb75e75cbf1a0f89ecf834fd787e8df90524825
status: current
---

# Event

## Purpose

The fundamental event entity. Every dated thing in Concorda is an
`Event`: a regatta race, a social party, a series race, a personal
calendar entry, a club meeting. Specialization happens via the
`category` field (`social`, `regatta`, `personal`) plus optional
joins to `Regatta`, `SailingEvent`, etc.

`Event` is heavily polymorphic. Many other models (`SailingEvent`,
`EventCrew`, `EventRegistration`, `EventDiscount`, `OrganizationEvent`,
`PersonEvent`, `EventRelationship`) reference an event by id. The
schedule, calendar feed, regatta detail, registrations, and most
activity surfaces are downstream of this row.

## Invariants

- **`date` is required, even if `start`/`end` are null.** `date` is
  the legacy column kept for SQLite compat; `start`/`end` are the new
  canonical columns. The `__init__` keeps them in sync — assign one,
  the other mirrors automatically. **Do not stop syncing them** until
  the legacy column is dropped.
- **`slug` is unique globally if non-null.** Personal events
  (`category == "personal"`) deliberately set `slug = None` to avoid
  global-uniqueness collisions across users. See commit `4fd165d`
  (`fix(events): drop slug for personal events to avoid global UNIQUE
  collision`).
- **All datetime columns use `UtcDateTime`** per
  `feedback_naive_datetime_convention`: stored naive-as-UTC, returned
  as aware datetime. Never `DateTime` directly.
- **`category` is one of `social`, `regatta`, `personal`** —
  `routers/events.py:29` defines `VALID_CATEGORIES = {"social",
  "regatta", "personal"}`. `personal` is the carve-out for user
  calendar entries that aren't club events.
- **`owner_id` is set only for personal events.** It identifies the
  user the event belongs to. For regatta and social events,
  ownership is via `OrganizationEvent`.

## Gotchas

- **Schedule queries that filter `Event.date >= today` will silently
  exclude personal events created in the past.** This bit twice (commit
  `7570175`, then revert `57f2e00`, then re-fix in `b887b73`). The
  right answer: schedule queries always include user-owned personal
  events regardless of date.
- **`category != "personal"` is the gate that hides personal events
  from public listing endpoints** (`routers/events.py:111, 134, 730,
  845`). Adding a new public listing endpoint? Add this filter or
  you'll leak personal events into the public surface.
- **Slug-null vs. slug-empty matters.** SQLite's UNIQUE constraint
  treats multiple NULLs as not-equal but multiple empty-strings as
  equal. Personal events MUST have `slug = None`, not `slug = ""`.
- **`source_event_id` chains personal events back to a public one**
  (when a user bookmarks a regatta into their schedule). Cascade
  semantics aren't formal — if the source is deleted, the personal
  copy lingers. Has bitten cleanup scripts.
- **`additional_data` JSON column is a freeform escape hatch.** Used
  for fields the canonical schema doesn't have yet. Treat as
  read-only unless you own the writing surface.

## Cross-cutting concerns

- **Auth**: most read endpoints are public; `personal` category gates
  on `owner_id == current_user.id` for visibility (events.py:89).
  Write endpoints typically require `events.create` or similar
  permission.
- **Schedule listing**: `Event.date` is the primary sort key but
  also needs comparison against current time for "upcoming" filters.
  Always compare in UTC; never use browser-local.
- **Logigraph rules touching this surface**: none directly yet, but
  `rule::event_crew::status_enum` and `rule::crew_visibility::*`
  reference EventCrew rows that belong to Events.
- **Calendar feed** (`/api/schedule/feed/{token}.ics`) emits events;
  the same date/category logic applies.

## External consumers

- **Concorda iOS app** consumes the events list and detail endpoints.
  Field renames here propagate; coordinate before adding required
  fields.
- **Calendar clients** (Google, Apple, Outlook) consume the .ics feed
  generated from `Event` rows.

## Open questions

- **When does the legacy `date`/`end_date` column get dropped?**
  `start`/`end` were added but the legacy columns are still required
  (`date` is `nullable=False`). The `__init__` sync is a transition
  shim. Migration TBD.
- **Should `location` move to a structured JSON address?** The
  comment at line 15 anticipates it. Currently free-form string.
- **Should `description` move to structured JSON content?** Same
  shape — comment at line 17 anticipates. Currently 2000-char string.
