---
node_id: concorda-api::models/organization_contact.py::OrganizationContact
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d81be85b6c2e899f5cce4351c0527a0b92030d0be6e5f8e1d94940606398e6c
status: current
---

# OrganizationContact

## Purpose

The `OrganizationContact` model defines the many-to-many relationship between an `Organization` and a `Person`. It acts as a join table that assigns a specific `role` (e.g., "Owner", "Admin", "Member") to a person within the context of a specific organization. Use this model when managing access control or contact lists for organization-level entities.

## Invariants

- **`organization_uuid` is required.** Every contact must be bound to a valid organization.
- **`person_uuid` is required.** Every contact must represent a specific person.
- **`role` is a non-nullable string.** It must be exactly 50 characters or fewer.
- **Inherits from `BaseModel`.** All instances must include the `type="OrganizationContact"` attribute via the constructor.

## Gotchas

- **Schema redesign in `ee82e42`.** This model is part of a recent structural overhaul involving new relationship tables and data migrations. Ensure any new queries or manual SQL scripts account for this specific table structure rather than assuming older relationship patterns.

## Cross-cutting concerns

- **Auth**: Relies on `organization_uuid` and `person_uuid` for permission checks in the API layer.
- **Audit**: Changes to this table (adding/removing contacts) are tracked via the `BaseModel` lineage.
- **Side effects**: Updates to this model may affect permission-based views in the dashboard and user-role visibility.

## External consumers

None known.
