---
node_id: concorda-api::models/organization_regatta.py::OrganizationRegatta
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ab3222e6675dd0b70834b434b93c1e3e0ad5fc51f9745b843daac547b7a4bc5b
status: llm_drafted
---

# OrganizationRegatta

## Purpose

Defines the many-to-many relationship mapping between an `Organization` and a `Regatta`. It acts as a join table that carries metadata about the specific nature of the connection via the `relationship` field and a `description` JSON blob. Use this model when establishing how an organization interacts with a specific regatta event, rather than using a generic association.

## Invariants

- **`organization_uuid` and `regatta_uuid` are mandatory.** Both must be valid 36-character strings (UUIDs) and are indexed for fast lookups.
- **`relationship` is a required string.** It defines the type of connection (e.g., "host", "participant") and has a maximum length of 50 characters.
- **Inherits from `BaseModel`.** This ensures standard fields like `created_at` or `updated_at` (if defined in the base) are present.
- **`description` is a JSON field.** It allows for flexible, unstructured metadata specific to the relationship without requiring schema migrations for every new attribute.

## Gotchas

- **Schema redesign requirement:** Per commit `ee82e42`, this model is part of a "new relationship tables" redesign. Do not attempt to revert to a single-table join or a simpler association; the current structure is required for the new data migration and model updates.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to this model may affect how organization-level permissions or visibility are calculated for regatta-specific events.

## External consumers

None known.
