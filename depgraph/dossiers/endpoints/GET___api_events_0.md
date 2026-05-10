---
node_id: GET::/api/events/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae139b2c618a16cc66ab28b34c9f52cbf744ceb2a024fa1b253b8a37b8268836
status: current
---

# GET /api/events/{event_id}

## Purpose

Fetches a single event's full details by its unique identifier. It is the primary read endpoint for event data, used to populate detailed views and schedules. It returns a specialized response shape via `_build_event_response` that includes nested regatta information.

## Invariants

- **Returns `EventReadWithRegatta`** — the response is a composite object containing the event and its associated regatta data.
- **Throws 404 if missing** — if the `event_id` does not exist in the database, an `HTTPException` with `detail="Event not found"` is raised.
- **Requires a valid `event_id` string** — the path parameter must be a string that matches the database identifier format.

## Gotchas

- **Personal events collision** — per commit `4fd165d`, the system dropped slugs for personal events to avoid global `UNIQUE` constraint collisions. Ensure the ID being queried is the correct identifier for the specific event type (global vs. personal).
- **Timezone rendering** — per commit `6c314f5`, while this endpoint returns the raw data, the consumer must handle the UTC-to-local conversion (e.g., for `.ics` or email bodies) to avoid displaying the wrong time to users in different zones.

## Cross-cutting concerns

- **Auth**: None (publicly readable, though visibility logic may be handled at the database query level in `_build_event_response`).
- **Side effects**: Used to populate the "schedule detail page" (per commit `23668de`).

## External consumers

- `concorda-web` (via `adminEventsApi.get` and `eventsApi.get`).
