---
node_id: GET::/api/events/upcoming
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7776dba0507151d1869ef3820119d68e5da971899cf858f24e4b0b75eea7033d
status: llm_drafted
---

# GET /api/events/upcoming

## Purpose

Fetches a list of upcoming events for the general public or organization-wide view. It filters for events occurring from the current UTC time forward, excluding those categorized as "personal". Use this endpoint for high-level event discovery (e.g., calendars, public lists) rather than the user-specific `/my-schedule` endpoint, which includes private/owned boat data.

## Invariants

- **HTTP Method**: `GET`
- **Path**: `/api/events/upcoming`
- **Query Parameters**: `limit` (int, 1-20, default 5), `region` (Optional string), `category` (Optional string).
- **Return Shape**: A list of `EventReadWithRegatta` objects.
- **Temporal Filter**: Automatically filters for `Event.date >= datetime.now(timezone.utc)`.

## Gotchas

- **Personal events are excluded by default.** The logic `if category: ... else: query.filter(Event.category != "personal")` ensures that unless a specific category is requested, "personal" events are hidden from the general upcoming list.
- **The `limit` is strictly capped.** The `ge=1, le=20` constraint on the `limit` parameter means callers cannot request more than 20 events at once.
- **Timezone-sensitive ordering.** Events are ordered by `Event.date`. Per commit `6c314f5`, ensure that any client-side rendering of these dates accounts for the organization's local time, as the API returns UTC.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible endpoint).
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

- `concorda-web` (via `eventsApi.upcoming`)
