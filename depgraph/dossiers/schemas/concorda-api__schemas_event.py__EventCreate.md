---
node_id: concorda-api::schemas/event.py::EventCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 547e6e7606a08da82f2a779af6ed1f7d50d35ddf79169f72f66a1df67e5cad19
status: current
---

# EventCreate

## Purpose

The schema for creating a new event via the API. It defines the required and optional fields for a single event entry, distinguishing itself from `EventUpdate` by requiring a `name` and `date`. It serves as the primary data contract for the `POST /api/events` endpoint.

## Invariants

- **`name` and `date` are required.** All other fields are optional to allow for flexible event creation.
- **`category` defaults to `"social"`.** If not provided, the event is categorized as a social event by default.
- **`organizing_authority_uuids` accepts a list of strings.** This allows for multi-OA (Organizing Authority) event structures.
- **`end_date` is an optional `datetime`.** It is not strictly enforced to be after `date` at the schema level, though business logic may require it.

## Gotchas

- **Multi-OA support is a recent addition.** Per commit `fdc87b4`, the schema was updated to support multiple Organizing Authorities, which is critical for the "my-schedule series" and "crew workflow" features.
- **`slug` is optional but often expected.** While the schema allows it to be `None`, many downstream consumers (like the schedule view) rely on a consistent URL structure.

## Cross-cutting concerns

- **Auth**: Used by `POST /api/events` which requires authenticated ownership/permissions.
- **Side effects**: Creating an event via this schema triggers updates to the "my-schedule" series and potentially the "crew workflow" logic.

## External consumers

- `POST /api/events` (via `routers/events.py`)
