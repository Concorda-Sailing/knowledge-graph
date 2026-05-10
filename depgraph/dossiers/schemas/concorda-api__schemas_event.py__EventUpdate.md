---
node_id: concorda-api::schemas/event.py::EventUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 06ae02be79d591c77bcd2d4c7d7453a77f00c9ca81f93c703f8877ea3eb47e15
status: llm_drafted
---

# EventUpdate

## Purpose

The `EventUpdate` schema defines the payload for partial updates to an existing event. Unlike `EventRead`, which is a full representation of the event state, this model uses `Optional` types for all fields to allow for patch-style updates where only the provided fields are modified. It is the primary schema used by the `PUT /api/events/{id}` endpoint to modify event metadata, scheduling, or organizational ownership.

## Invariants

- **All fields are `Optional`** — This allows the API to distinguish between a field being "not provided" (no change) and "provided as null" (depending on how the router handles the patch).
- **`category` defaults to `"social"`** — If not explicitly provided in the update payload, the underlying logic should respect the default value or the existing value.
- **`organizing_authority_uuids` expects a list of strings** — Updates to this field must provide the full list of UUIDs to avoid accidental deletion of existing authorities.
- **`price` uses `Decimal`** — Any numeric updates to the price must maintain decimal precision to avoid floating-point errors in financial calculations.

## Gotchas

- **Schema mismatch in regatta flows** — Per commit `33ebcf6`, the relationship between events and regattas is evolving (regatta-as-child-of-event). Ensure that updating an event via this schema does not inadvertently strip regatta-specific metadata if the implementation relies on `EventReadWithRegatta` logic.
- **Multi-OA complexity** — Recent work in `fdc87b4` (events multi-OA) implies that `organizing_authority_uuids` is a critical field for access control. Changing this list via `EventUpdate` directly impacts which authorities can manage the event.

## Cross-cutting concerns

- **Auth**: Dependent on the `PUT /api/events/{id}` router; requires appropriate ownership/authority permissions to execute the update.
- **Side effects**: Updates to `date` or `end_date` may trigger notifications or updates to the "my-schedule" view (per `fdc87b4`).

## External consumers

- `PUT /api/events/{id}` (via `routers/events.py:1295`)
