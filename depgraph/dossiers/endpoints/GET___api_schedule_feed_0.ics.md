---
node_id: GET::/api/schedule/feed/{0}.ics
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e023f3c9225cc0474db064fd29dd6bad1dda687c2767903c133ef98af63a4779
status: llm_drafted
---

# GET /api/schedule/feed/{token}.ics

## Purpose

Generates a standard `.ics` calendar feed for a specific user via a unique `calendar_token`. This provides a way for users to sync their personal sailing schedule (including regattas, crew commitments, and boat-specific logistics) into external calendar applications. It is distinct from the standard `/api/events/my-schedule` endpoint because it transforms internal event data into a valid iCalendar format with localized timezones and specific `DTSTART`/`DTEND` logic.

## Invariants

- **Auth via Token Possession**: No Bearer token is required; the presence of a valid `calendar_token` in the URL path is the sole mechanism for identity.
- **Returns `text/calendar`**: The response must have `media_type="text/calendar; charset=utf-8"` and a `Content-Disposition` of `inline`.
- **Cache-Control**: The response is cached for 300 seconds (`max-age=300`) to reduce database load on frequent external polling.
- **Fallback Identity**: If `org_name` or `timezone` are missing from `OrgConfig`, the feed defaults to `"Sailing Schedule"` and `"America/New_York"`.
- **404 on Missing Token**: If the token does not exist, the API returns a 404 to prevent leaking whether a token is valid or simply non-existent.

## Gotchas

- **Timezone Localization**: Per commit `6c314f5`, the feed must render the `.ics` body in the organization's timezone, not UTC. Failing to use the `tz_id` from `OrgConfig` in `build_schedule_feed_ics` will result in incorrect event times in external calendars.
- **Privacy/Leakage Guard**: Per commit `ef306eb`, the function must scope `SailingEvent` lookups using `owned_boat_ids` and `viewer_event_crew_se_ids`. This prevents a user from seeing the specific logistics/dock times of a stranger's event through the feed.
- **Event Timing Logic**: Events with no `dock_time` are rendered as all-day events. For timed events, the `DTEND` is calculated as `arrival_time` if set, otherwise `dock_time + estimated_duration`, or a fallback of `dock_time + 2h`.

## Cross-cutting concerns

- **Auth**: None (Identity is derived from the `token` path parameter).
- **Rate limit**: None.
- **Side effects**: External calendar apps (Google, Apple, Outlook) poll this endpoint to update user schedules.

## External consumers

External calendar applications (Google Calendar, Apple Calendar, etc.) via the provided `.ics` URL.
