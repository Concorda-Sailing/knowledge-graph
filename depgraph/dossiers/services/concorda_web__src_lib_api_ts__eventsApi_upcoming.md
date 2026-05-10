---
node_id: concorda-web::src/lib/api.ts::eventsApi.upcoming
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c0b8d4acf5561998d7d7d897f509d2e53ce8b2c3a2084bf409ca5d852d32b3d9
status: llm_drafted
---

# eventsApi.upcoming

## Purpose

Fetches a limited list of upcoming events, optionally filtered by region or category. This is the primary method for populating high-level event lists and dashboards. Use this instead of `list()` when you need a small, curated subset of upcoming-focused data rather than a full-range search.

## Invariants

- **Returns `Event[]`** — the response is a collection of event objects.
- **Default limit is 5** — if no limit is provided, the API returns a small default set.
- **Uses `fetchApi`** — unlike `getDetail` or `checkin`, this is a public/unauthenticated endpoint.
- **Query parameters are stringified** — `limit` is explicitly cast to a string in the URL.

## Gotchas

- **Recent logic changes in `schedule`** — per commit `2d6b8a7`, the display of event counts (like "accepting-crew") is driven by per-race toggles, but this method only fetches the event skeleton; it does not include the live count logic itself.
- **Schema-matching sensitivity** — per commit `bf15808`, ensure any changes to the `Event` type do not break the implicit shape-matching expected by the dashboard components that consume this list.

## Cross-cutting concerns

- **Auth**: None (public endpoint).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Directly populates the `UpcomingEvents` component in the dashboard.

## External consumers

- `concorda-web::src/components/dashboard/upcoming-events.tsx` (UpcomingEvents component).
