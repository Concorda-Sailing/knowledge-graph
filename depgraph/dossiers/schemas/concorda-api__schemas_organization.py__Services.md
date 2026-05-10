---
node_id: concorda-api::schemas/organization.py::Services
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 71fede1365c70454fa0e02f2544b1b835fb28f06ac44d7282706a28f9038d984
status: llm_drafted
---

# Services

## Purpose

Defines the availability status for specific amenities within an organization. It is a sub-model used by `OrganizationCreate` to capture boolean flags for services like dockage, moorings, food, and lodging. This is distinct from the broader `Organization` models which handle identity and contact info; `Services` is strictly for amenity availability toggles.

## Invariants

- **All fields are boolean.** `dockage_available`, `moorings_available`, `food`, and `lodging` must be boolean values.
- **Default values are `False`.** If not explicitly provided during creation, all service flags default to `False`.
- **Nested in `OrganizationCreate`.** This model is intended to be passed as the `services` field within the larger organization creation payload.

## Gotchas

- **Implicit False vs. Missing.** Because the fields default to `False`, a client cannot currently distinguish between "the user explicitly turned this off" and "the user didn't provide the field." This may cause issues if the API evolves to support optional amenities that are not yet available.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to these flags may impact how organizations are filtered in search/discovery features (e.g., "organizations with dockage").

## External consumers

None known.
