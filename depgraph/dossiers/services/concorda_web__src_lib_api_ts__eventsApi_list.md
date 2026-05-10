---
node_id: concorda-web::src/lib/api.ts::eventsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3622c6625ef2fc9494bf69d16856af7f224f2d197c6c02150c4187b3a2f4fd2f
status: current
---

# eventsApi.list

## Purpose

The `eventsApi.list` method provides a way to fetch collections of events with optional filtering by date range or geographic region. It is the primary entry point for public-facing event discovery, used by both the main event landing pages and the members-only event views. Use this when you need a list of events rather than a specific single event or a filtered subset like "upcoming" events.

## Invariants

- **Returns `Event[]`** — the response is an array of event objects.
- **Query parameters are optional** — `start_date`, `end_date`, and `region` are all optional; if omitted, the API returns the default unfiltered list.
- **Uses `fetchApi`** — this is a public-facing, unauthenticated call (unlike `getDetail` or `registerAuthenticated`).
- **URL construction** — parameters are appended via `URLSearchParams` to ensure correct encoding of the query string.

## Gotchas

- **Decoupling from `mySchedule`** — per commit `1b5d864`, this method (and the broader events API) no longer relies on the `mySchedule` coupling. Ensure you are not attempting to pass user-specific schedule state through this list call.
- **Status-based visibility** — per commit `2d6b8a7`, the visibility of certain event details (like "accepting-crew" status) is driven by the underlying regatta configuration, not by the list call itself.
- **Parameter types** — `start_date` and `end_date` must be valid date strings compatible with the API's expected format to avoid silent failures in filtering.

## Cross-cutting concerns

- **Auth**: None. This is a public-facing endpoint.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `PublicEventsPage` in both `src/app/events/page.tsx` and `src/app/members/events/page.tsx` to populate event lists.

## External consumers

None known.
