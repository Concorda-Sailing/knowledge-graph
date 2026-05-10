---
node_id: concorda-api::models/person_regatta.py::PersonRegatta
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3a031c275959efa63b4c450f5330cfdc09838f3775eda64587df07c59e497cd7
status: current
---

# PersonRegatta

## Purpose

Defines the join-table relationship between a `Person` and a `Regatta`. It captures the specific role or `relationship` a person holds within a regatta context (e.g., competitor, coach, or official) and allows for unstructured metadata via the `description` JSON field. This is a distinct entity from `CrewPool`, which manages group-level compositions; `PersonRegatta` is used for individual-to-event assignments.

## Invariants

- **`person_uuid` and `regatta_uuid` are required.** Both must be valid 36-character UUID strings.
- **`relationship` is a non-nullable string.** It must be populated to define the person's role.
- **`description` is a nullable JSON field.** It stores arbitrary metadata (e.g., specific roles or notes) and must be handled as a dictionary in the application layer.
- **Inherits from `BaseModel`.** Every instance automatically includes a `type="PersonRegatta"` attribute via the `__init__` method.

## Gotchas

- **Schema redesign impact:** Per commit `ee82e42`, this model is part of a recent schema redesign involving new relationship tables and data migrations. Any changes to the `relationship` string format or the `description` JSON structure must be coordinated with the migration scripts to avoid breaking existing person-regatta associations.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None known.

## External consumers

None known.
