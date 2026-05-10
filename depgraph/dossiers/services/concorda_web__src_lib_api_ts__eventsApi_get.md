---
node_id: concorda-web::src/lib/api.ts::eventsApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a0ced854073e32a20ca67b0bd8ee6f2fce303dca5b564a8528365941dbccf216
status: current
---

# eventsApi.get

## Purpose

The primary method for fetching a single event by its unique ID. It is the base fetcher for event-specific detail views, whereas `getBySlug` should be used for public-facing URL-driven navigation. Use `getDetail` instead if you need the viewer-scoped metadata (e.g., `sailing_event` or `viewer_role`) required for the schedule detail page.

## Invariants

- **Returns a single `Event` object.**
- **Uses `fetchApi` (unauthenticated).** This method does not require a bearer token, making it suitable for public-facing event pages.
- **Input is a string `id`.**

## Gotchas

- **`get` vs `getDetail` distinction.** Per commit `1b5d864`, the detail page was refactored to call `/api/events/{id}/detail` to drop the coupling to `mySchedule`. If you need to show user-specific status (like "bookmarked" or "crew"), you must use `getDetail` instead of `get`.
- **`get` does not return viewer-scoped data.** If a component relies on `get` to determine if a user is a "crew" member or "owner," it will fail to find that information because `get` is unauthenticated and returns the base `Event` shape.

## Cross-cutting concerns

- **Auth**: None (uses `fetchApi`).
- **Side effects**: Used by the "schedule detail page" to render core event data.

## External consumers

None known.

## Open questions

- Should there be a distinction in the type signature between a public `Event` and the `ScheduleItem` returned by `getDetail` to prevent developers from accidentally using the wrong one in authenticated views?
