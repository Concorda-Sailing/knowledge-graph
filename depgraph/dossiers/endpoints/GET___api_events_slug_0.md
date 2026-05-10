---
node_id: GET::/api/events/slug/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cb217c5d4cb5ead0acfd93acd0e993baeac9a5d95a17a43e8573c86549fc0d75
status: llm_drafted
---

# GET /api/events/slug/{slug}

## Purpose

Fetches a single event's full details using its unique string slug. This is the primary entry point for the web app to load a specific event page (e.g., a regatta or personal cruise) without requiring the client to know the internal UUID. It serves as the data provider for the event detail view.

## Invariants

- **Returns `EventReadWithRegatta`** — the response shape includes nested regatta data and is strictly typed.
- **Requires a valid `slug` string** — the lookup is performed via `Event.slug`.
- **Throws 404 if not found** — if the slug does not match an existing event, the API returns a 404 error.
- **Uses `_build_event_response`** — all serialization logic and database-to-model mapping is centralized in this helper.

## Gotchas

- **Slug collisions for personal events** — per commit `4fd165d`, the system dropped the slug for personal events to avoid global `UNIQUE` constraint collisions. If you are looking for a way to identify a personal event via a slug, ensure it follows the new non-colliding pattern.
- **Date filtering logic** — while this endpoint is a direct fetch, related schedule logic (like in `get_my_schedule`) uses a `schedule_floor` to prevent events created earlier today from "vanishing." Ensure any client-side logic relying on "upcoming" events accounts for this UTC-start-of-day behavior.

## Cross-cutting concerns

- **Auth**: None (publicly accessible via slug).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.getBySlug` (Primary web client consumer).
- `concorda-test::lib/api-client.ts::ApiClient.getEventBySlug` (Test suite dependency).
