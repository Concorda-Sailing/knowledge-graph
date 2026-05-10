---
node_id: POST::/api/events/my-schedule/add-events
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 31d375f3f39aefafdf76521ab96722d622c2f748a3957621ea65d7eb18502757
status: llm_drafted
---

# POST /api/events/my-schedule/add-events

## Purpose

Creates personal copies of existing events to populate a user's personal schedule. It takes a list of source event IDs, clones their core attributes (name, date, location, etc.), and assigns them to the authenticated user with the category set to `"personal"`. This allows users to "bookmark" or "track" events without modifying the original source event.

## Invariants

- **Requires `require_auth`** — The `current_user` is injected via dependency and must be authenticated.
- **Input is `AddEventsToSchedule`** — Expects a JSON body with `event_ids: list[str]`.
- **Returns a summary object** — Returns `{"added": int}` (and potentially `sailing_events_created` depending on the specific implementation branch, though the current source shows `{"added": added}`).
- **Idempotency via `source_event_id`** — If a user attempts to add an event that already exists in their schedule (matching `owner_id`, `category="personal"`, and `source_event_id`), the function skips that ID rather than creating a duplicate.

## Gotchas

- **Slug Collisions** — Per commit `4fd165d`, personal events must not use the same slug as source events to avoid global `UNIQUE` constraint violations in the database.
- **Date Filtering** — Per commit `559491c`, the schedule logic (which consumes these events) is sensitive to date filters; ensure the cloned event's date is valid for the user's intended view.
- **Ownership vs. Source** — This endpoint creates a *copy*. It does not modify the original `Event` record, ensuring that adding an event to a personal schedule doesn't inadvertently change the master event's data.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the `current_user`.
- **Side effects**: Populates the user's personal schedule, which is surfaced in the "my-schedule" views and the personal calendar.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.addEvents` (used by the web frontend to allow users to add events to their schedule).
