---
node_id: concorda-api::utils/ics_utils.py::build_feed_ics
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 46168c18bd7d78ae5c0290b12842671f0f3025664a633ba9d372f9cc52ebf704
status: current
---

# build_feed_ics

## Purpose

A legacy wrapper for generating iCalendar (.ics) feeds. It converts `CrewIcsContext` objects into `FeedItem` instances and delegates to `build_schedule_feed_ics`. It exists solely for backward compatibility to prevent breaking imports from older modules that specifically expect the `CrewIcsContext` signature.

## Invariants

- **Delegates to `build_schedule_feed_ics`** — This function does not perform the actual string assembly or line folding; it only prepares the `FeedItem` list.
- **Returns a CRLF-terminated string** — The final output is a single string formatted for iCalendar compatibility.
- **Uses `DEFAULT_TZID` as a fallback** — If no specific timezone is successfully extracted from the context, it defaults to the system constant.

## Gotchas

- **Deprecated usage** — Per the docstring and source, this is a "Legacy alias." New implementations must use `build_schedule_feed_ics` with `FeedItem` directly to avoid the overhead of the `CrewIcsContext` translation.
- **Timezone-aware rendering** — Per commit `6c314f5`, this function (via its delegation) must ensure the `.ics` body reflects the organization's timezone rather than UTC to prevent calendar drift for users.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
