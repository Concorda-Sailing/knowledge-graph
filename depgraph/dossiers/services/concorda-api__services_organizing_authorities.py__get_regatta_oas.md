---
node_id: concorda-api::services/organizing_authorities.py::get_regatta_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 437c7bb3bf8ae904c055d95b727350321fee8401acedec2a5bfb1d8f1048c2ee
status: current
---

# get_regatta_oas

## Purpose

Retrieves the list of Organizing Authorities (OAs) associated with a specific Regatta. It uses the `_get_oas` helper to query the `OrganizationRegatta` join model, identifying which organizations have authority over the given `regatta_uuid`. This is distinct from the `get_event_oas` or `get_series_oas` methods, which target different levels of the hierarchy.

## Invariants

- **Input is a `regatta_uuid` string.** The function expects a valid UUID representing a regatta entity.
- **Returns a `list[dict]`.** The output is a list of dictionaries representing the organization records associated with the regatta.
- **Uses `OrganizationRegatta` as the join model.** The lookup is strictly bound to the relationship defined in the `OrganizationRegatta` table.

## Gotchas

- **Scope enforcement dependency.** Per commit `058aa8c`, this logic is part of the tier-C cross-org scope enforcement. Any changes to how OAs are retrieved must ensure they do not bypass the intended organizational boundaries.

## Cross-cutting concerns

- **Auth**: Relies on the caller to enforce scope via the returned list of organization IDs.
- **Audit**: N/A.

## External consumers

None known.
