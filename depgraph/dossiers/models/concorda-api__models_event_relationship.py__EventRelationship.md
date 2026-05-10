---
node_id: concorda-api::models/event_relationship.py::EventRelationship
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 73cc571fc18c8a1164b737ad5cbbcd0c2bd1bfa31169cb46a48c780a5d23ece1
status: current
---

# EventRelationship

## Purpose

Defines the schema for linking two events or an event to a regatta. It is used to represent complex associations like crew suggestions or hierarchical event structures. This model is distinct from `CrewPool` as it focuses on the structural relationship between entities rather than the membership of a specific pool.

## Invariants

- **`from_event_uuid` is mandatory.** It must be a valid 36-character UUID string.
- **`relationship` is a required string.** It defines the type of connection (e.g., "suggestion", "parent-child").
- **`to_event_uuid` and `to_regatta_uuid` are nullable.** A relationship can point to an event, a regatta, or both (though logic usually dictates one or the other).
- **`description` is a JSON object.** It allows for arbitrary metadata associated with the relationship.

## Gotchas

- **Schema is in flux.** Per commit `ee82e42` ("Schema redesign: new relationship tables, data migration, model updates"), this model is part of a recent structural overhaul. Any changes to the `relationship` string values or the JSON structure in `description` must be coordinated with the migration scripts to avoid breaking the `GET /api/events/{0}/sailing-event/crew-suggest` endpoint.

## Cross-cutting concerns

- **Auth**: None (though the endpoint using this model requires authentication).
- **Side effects**: Directly impacts the output of the `crew-suggest` endpoint in `routers/events.py`.

## External consumers

- `GET::/api/events/{0}/sailing-event/crew-suggest` (via `db_query`).
