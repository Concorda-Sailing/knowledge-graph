---
node_id: concorda-api::utils/ics_utils.py::build_schedule_feed_ics
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 370e1f3b60ae404c3d964b671e9205e67c8ed604c6f8e3a36a46e365389080fc
status: current
---

# build_schedule_feed_ics

## Purpose

Generates a standardized iCalendar (ICS) string for the per-user webcal feed. It transforms a collection of `FeedItem` objects into a single `PUBLISH` method calendar. Use `build_schedule_feed_ics` for all new implementations; `build_feed_ics` is a legacy alias that wraps `CrewIcsContext` and should be avoided for new logic.

## Invariants

- **Method is `PUBLISH`** — The generated calendar uses the `PUBLISH` method to ensure clients treat it as a subscription feed.
- **`tz_id` must be the organization's timezone** — The `tz_id` passed must match the `OrgConfig.timezone` to ensure event times are rendered correctly in the user's calendar app.
- **Returns a CRLF-terminated string** — The output is a single string joined by `CRLF` and ends with a trailing `CRLF` to comply with the ICS spec.
- **`X-WR-TIMEZONE` is required** — The function explicitly injects the `tz_id` into the `X-WR-TIMEZONE` header to prevent client-side timezone drift.

## Gotchas

- **Timezone drift** — Per commit `6c314f5`, the feed must render in the organization's timezone rather than defaulting to UTC. Failing to pass the correct `tz_id` (derived from `OrgConfig.timezone`) causes events to appear at the wrong local time in external calendar clients.
- **Event deletion behavior** — Per docstring, removed events are not "deleted" in the traditional sense; the `UID` is simply omitted from the next refresh, causing clients to drop the event.

## Cross-cutting concerns

- **Auth**: None (this is a pure string generator).
- **Side effects**: The output is consumed by the `GET /api/schedule/feed/{0}.ics` endpoint to provide the webcal subscription for users.

## External consumers

- External calendar clients (Google Calendar, Apple Calendar, Outlook) via the `/api/schedule/feed/{0}.ics` endpoint.
