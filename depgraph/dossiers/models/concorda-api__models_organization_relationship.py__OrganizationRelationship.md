---
node_id: concorda-api::models/organization_relationship.py::OrganizationRelationship
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5cc3f1633dfc0662ad8b79595f40522844b067272d69475903c05b4ae5b303f2
status: current
---

# OrganizationRelationship

## Purpose

Defines the many-to-many relationship between two organizations. It is used to model complex hierarchies, such as parent-subsidiary links or service-level agreements, where a simple ownership flag on the `Organization` model is insufficient. Use this model when a relationship requires metadata (via the `description` field) rather than just a boolean flag.

## Invariants

- **`from_org_uuid` and `to_org_uuid` are mandatory.** Both must be valid 36-character UUID strings.
- **`relationship` is a required string.** It defines the type of connection (e.g., "parent", "partner", "vendor").
- **`description` is an optional JSON field.** It is used to store structured metadata about the relationship.
- **Inherits from `BaseModel`.** This ensures the `type="OrganizationRelationship"` is automatically injected into the constructor.

## Gotchas

- **Schema redesign requirement.** Per commit `ee82e42`, this model is part of a recent schema redesign involving new relationship tables and data migrations; ensure any new relationship types are compatible with the existing migration path.

## Cross-cutting concerns

- **Auth**: Access is governed by the `Organization` ownership/permission logic (see `Organization` model).
- **Audit**: Changes to relationships are tracked via the standard `BaseModel` audit trail.

## External consumers

None known.
