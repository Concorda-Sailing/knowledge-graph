---
node_id: concorda-api::models/organization_series.py::OrganizationSeries
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ffabd61f7c2177c2673c25f12b210d951c41916ec1d316bc34b5125ba28fbd36
status: llm_drafted
---

# OrganizationSeries

## Purpose

Defines the database schema for grouping organizational entities into specific series or relationships. It acts as a join-table/metadata layer that links an `organization_uuid` to a `series_uuid` via a specific `relationship` string. This model is used to categorize entities (like crew pools or merchandise) under a unified organizational umbrella.

## Invariants

- **`organization_uuid` and `series_uuid` are required.** Both must be valid 36-character strings.
- **`relationship` is a mandatory string.** It defines the type of connection between the organization and the series (max 50 chars).
- **`description` is a JSON field.** It allows for unstructured metadata storage, but must be a dictionary or null.
- **Inherits from `BaseModel`.** Like other models in this module, it must initialize with `type="OrganizationSeries"` to satisfy the base class constructor.

## Gotchas

- **Schema is part of a recent redesign.** Per commit `ee82e42`, this model is part of a "Schema redesign" involving new relationship tables and data migrations; ensure any new fields added here are compatible with the migration patterns established in that commit.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None known.

## External consumers

None known.
