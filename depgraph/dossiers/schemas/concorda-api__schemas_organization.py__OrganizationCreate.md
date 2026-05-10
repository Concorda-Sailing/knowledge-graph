---
node_id: concorda-api::schemas/organization.py::OrganizationCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fb5d6547ba1ecc515c757b34a5adab3d519593d48799a8222d461bc40ef51638
status: llm_drafted
---

# OrganizationCreate

## Purpose

The Pydantic model for creating or updating an organization. It defines the required and optional fields for initializing an organization entity via the API. Use this instead of `OrganizationRead` when performing `POST` or `PUT` operations to ensure the client does not attempt to inject read-only fields like `id`, `created`, or `modified`.

## Invariants

- **`name` is required.** It is a non-optional string.
- **`org_type` is required.** It is a non-optional string.
- **`social_media` and `services` are nested models.** They must follow the structure of `SocialMedia` and `Services` respectively.
- **`reciprocity_with` is a list of strings.** It expects a list of identifiers/names.

## Gotchas

- **`abbreviation` is a recent addition.** Per commit `bbe1627`, this field was added to support the organization abbreviation column. Ensure any client-side creation logic includes this field if the UI requires it.
- **`parent_org_id` is a string-based reference.** While not explicitly typed as a UUID, it is used to establish hierarchical relationships between organizations.

## Cross-cutting concerns

- **Auth**: Dependent on the organization router's authentication guards.
- **Side effects**: Changes to this schema via `POST /api/organizations` or `PUT /api/organizations/{0}` will update the organization record used by the crew-finder and schedule systems.

## External consumers

- `POST /api/organizations`
- `PUT /api/organizations/{0}`
