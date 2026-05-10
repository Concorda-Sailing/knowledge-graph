---
node_id: concorda-api::models/person_permission.py::PersonPermission
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 67e66c1adfc7161d7e6f23a180b9310758860d3c3770dac97729bd277a4a35c5
status: llm_drafted
---

# PersonPermission

## Purpose

Defines the database schema for mapping a specific person to a permission via a UUID-based relationship. It acts as the join-table representation for granular access control, linking a `person_uuid` to a `permission_uuid`. This is distinct from role-based access (which uses `granted_by_role_uuid`) and is used when permissions are granted directly to individuals rather than via a role.

## Invariants

- **`person_uuid` and `permission_uuid` are mandatory.** Both must be valid 36-character UUID strings.
- **`person_uuid` and `permission_uuid` are indexed.** Both fields use `index=True` to ensure fast lookups during permission checks.
- **`granted_by_role_uuid` is nullable.** This field is optional and allows the system to track if a permission was inherited from a role or granted directly.
- **Inherits from `BaseModel`.** This ensures the model includes the standard `type="PersonPermission"` field required for polymorphic serialization/deserialization.

## Gotchas

- **Schema redesign dependency.** Per commit `ee82e42`, this model is part of a recent "Schema redesign" involving new relationship tables and data migrations. Any changes to the UUID field lengths or types must be reconciled with the migration scripts introduced in this commit.

## Cross-cutting concerns

- **Auth**: Indirectly affects authorization logic; used to determine if a person has a specific permission.
- **Audit**: N/A
- **Side effects**: Changes to this table may affect permission-checking logic in the API layer.

## External consumers

None known.
