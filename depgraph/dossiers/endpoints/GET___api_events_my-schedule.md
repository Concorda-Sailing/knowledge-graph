---
node_id: GET::/api/events/my-schedule
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5dd568f5a0581aebdba2ec22d716efe3cb228b665ba6c53e403348dc1f749ca0
status: current
---

# GET /api/events/my-schedule

## Purpose

Retrieves a personalized, upcoming schedule for the authenticated user. It aggregates three distinct types of events: personal events owned by the user, bookmarked events (via `PersonEvent`), and events the user is registered for (via `EventRegistration`). This is the primary source for the user's personal calendar view and the "My Schedule" dashboard.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a `list[dict]`** containing event data and associated sailing details.
- **Filters by `schedule_floor`** — events are only returned if their date is on or after the start of the current UTC day.
- **Includes co-owned boat context** — the response includes logic to identify boats where the user is an active owner alongside at least one other person.

## Gotchas

- **Date flooring is critical** — per commit `559491c`, the filter is floored at the start-of-today UTC. This ensures that events created earlier in the same day (e.g., a personal cruise added at noon for an 11am dock time) do not vanish from the schedule immediately after being saved.
- **Avoided a recent regression** — commit `57f2e00` reverted a change that incorrectly excluded user-owned personal events based on date; the current implementation ensures owned events are always included regardless of the specific time-of-day.
- **"Shared" badge logic** — per the logic in the source, the "Shared" badge is only surfaced if the boat is co-owned (≥2 active owners). Sole-owned boats do not trigger this, as the user reaches those events through personal/bookmarked buckets.
- **Slug collision avoidance** — per commit `4fd165d`, personal events do not use slugs to avoid global `UNIQUE` constraint collisions in the database.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to establish `current_user`.
- **Side effects**: Updates to `EventRegistration` or `PersonEvent` (the sources for this list) will immediately change the output of this endpoint.

## External consumers

- `concorda-web` (via `eventsApi.mySchedule`)
- `concorda-test` (via `ApiClient.listMySchedule`)
