---
node_id: concorda-api::models/person_boat.py::PersonBoat
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b915b9aed2c113f4f71a0769b867d2aa4f7e6bf85f9abc6fe73bda214eb0c3c
status: current
---

# PersonBoat

## Purpose

The `PersonBoat` model defines the many-to-many relationship between a person and a boat, specifically capturing the nature of their connection (e.g., owner, crew, or guest). It serves as the join table for the `person_uuid` and `boat_uuid` identifiers. This is a distinct entity from `CrewPool`, which manages group-level assignments, whereas `PersonBoat` is used for granular, individual-level relationship tracking.

## Invariants

- **`person_uuid` and `boat_uuid` are required.** Both must be valid 36-character UUID strings.
- **`relationship` is a mandatory string.** It must be exactly 50 characters or fewer.
- **`description` is a JSON field.** It accepts a dictionary or `None` for storing unstructured metadata about the relationship.
- **Inherits from `BaseModel`.** The `__init__` method automatically sets `type="PersonBoat"` via the superclass.

## Gotchas

- **Schema redesign requirement.** Per commit `ee82e42`, this model is part of a recent "new relationship tables" migration; ensure any new relationship-based logic accounts for this specific table structure rather than the legacy direct-association patterns used previously.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None known.

## External consumers

None known.
