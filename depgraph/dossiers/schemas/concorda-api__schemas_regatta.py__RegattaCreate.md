---
node_id: concorda-api::schemas/regatta.py::RegattaCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7e97d099d2c781ed213e515917324991e2664f373c316293ac308d0801636ba
status: llm_drafted
---

# RegattaCreate

## Purpose

Defines the input schema for creating a new regatta via the `POST /api/regattas` endpoint. It captures the core identity and logistical metadata of a regatta, distinguishing it from `RegattaUpdate` (which allows partial updates) and `RegattaRead` (which includes system-generated fields like `id` and `slug`).

## Invariants

- **`name` is required.** All other fields are optional to allow for flexible creation flows.
- **`start` and `end` are optional.** These are `datetime` objects; if provided, they must follow ISO 8601 format.
- **`organizing_authority_uuids` is a list of strings.** This allows a single regatta to be associated with multiple OAs.
- **`rc_channel` is an integer.** This is used for radio communication coordination.

## Gotchas

- **Per commit `6c9b5f3`, the relationship between race toggles and boat counts is sensitive.** While this schema defines the regatta, the logic for how "per-race toggles" drive `Accepting-Crew` status affects how boats are displayed on the calendar.
- **`MatchCounts` dependency.** While not a direct field in `RegattaCreate`, the recent commit `e1c7e44` indicates that backend logic for regatta match counts is a critical part of the regatta lifecycle.

## Cross-cutting concerns

- **Auth**: Required for the `POST /api/regattas` endpoint.
- **Side effects**: Creating a regatta via this schema populates the data used by the "on-calendar boats" display and the "Accepting-Crew" status logic.

## External consumers

- `POST /api/regattas` (routers/regattas.py)
