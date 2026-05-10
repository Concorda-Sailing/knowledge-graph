---
node_id: concorda-api::schemas/boat.py::BoatEventRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1323241e8896b9d9b8f52c99b9df2205510f4e9d6bfadd9b850cd363195811e8
status: llm_drafted
---

# BoatEventRead

## Purpose

The read-only schema for boat-related event data. It provides a flattened view of an event, combining identity information (`intent_id`, `regatta_uuid`) with descriptive metadata (`event_name`, `event_date`) and resource requirements (`positions_needed`, `positions_offered`). Use this schema when returning event details via the `GET /api/boats/{boat_id}/events` endpoint to ensure the UI has enough context to render a schedule without making secondary lookups for regatta or event names.

## Invariants

- **`intent_id` and `regatta_uuid` are required strings.** These act as the primary keys for navigating the relationship between a boat, its parent regatta, and the specific intent.
- **`intent` and `status` are non-optional strings.** Every event must have a defined intent (e.g., "participation") and a status (e.g., "confirmed") to be valid in the UI.
- **`positions_needed` and `positions_offered` are `list[str]`.** If no positions are present, these must be returned as `None` (null in JSON) rather than an empty list, per the `Optional` type hint.

## Gotchas

- **Schema expansion is frequent.** Per commit `68a7508`, recent migrations and "router refinements" suggest that the structure of boat-related data is still evolving alongside the crew roster service.
- **Implicit dependency on `regatta_name` and `event_name`.** While these are `Optional`, the UI relies on them for display. If the underlying `EventRead` or `Regatta` objects change, this flattened schema may surface stale or null values if the join logic in the router isn't updated.

## Cross-cutting concerns

- **Auth**: None (this is a pure data schema).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The `GET /api/boats/{0}/events` endpoint (the primary consumer) drives the rendering of the boat's event schedule in the dashboard.

## External consumers

- `GET /api/boats/{0}/events` (internal API router).
