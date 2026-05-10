---
node_id: concorda-api::schemas/regatta.py::RegattaUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fb8256a9282d55750a80a0d4b858165d04db60b7b11865d9d95c038c0371cbb7
status: current
---

# RegattaUpdate

## Purpose

The `RegattaUpdate` schema defines the payload for updating existing regatta metadata. It is a partial update model where all fields are optional, allowing clients to patch specific attributes (like `name`, `location`, or `start` time) without providing the full object. It is distinct from `RegattaRead`, which includes system-generated fields like `id`, `created`, and `match_counts`.

## Invariants

- **All fields are `Optional`** — The schema is designed for PATCH-style updates; omitting a field in the request does not nullify the existing value in the database, but rather leaves it unchanged.
- **`oa_uuid` and `region_uuid` are strings** — These must be valid UUIDs for the respective entities to maintain relational integrity during an update.
- **`scoring_system` expects a list** — While the type is `list`, the implementation must ensure the input is a valid list of scoring rules to avoid runtime errors in the processing engine.

## Gotchas

- **`start` and `end` must be UTC-compatible** — Per the pattern in `RegattaRead`, these are `datetime` objects; passing malformed strings will fail validation before reaching the database.
- **`additional_events` and `organizing_authority_uuids` are list-based** — Ensure that updates to these fields replace the existing list rather than appending to it, as is standard for Pydantic-based partial updates in this API.

## Cross-cutting concerns

- **Auth**: Requires authenticated access via the `PUT /api/regattas/{0}` endpoint.
- **Side effects**: Updates to this schema trigger changes in the regatta's visibility on the calendar and may affect the `match_counts` displayed in the `RegattaRead` view.

## External consumers

- `PUT /api/regattas/{0}` (via `routers/regattas.py:203`)
