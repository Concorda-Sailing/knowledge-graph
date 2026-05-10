---
node_id: concorda-api::services/organizing_authorities.py::get_oas_bulk
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7e4e4f522d689f3778520096baf1e2236902f9349ea04e93876967219c0d5e90
status: llm_drafted
---

# get_oas_bulk

## Purpose

Fetches summarized data for Organizing Authorities (OAs) associated with a batch of parent entities (e.g., Products or Events) in a single database round-trip. It uses a dynamic `join_model` and `fk_field` to allow the same logic to resolve OAs across different entity types. Use this instead of individual lookups when populating lists or dashboards that display parent-related organizational context.

## Invariants

- **Input `parent_uuids` must be a list of strings.** If an empty list is passed, the function returns an empty dictionary `{}`.
- **`join_model` must have a `organization_uuid` column.** The query relies on this specific attribute to perform the join.
- **`fk_field` must be a valid attribute on `join_model`.** This field is used via `getattr` to establish the relationship link.
- **Returns a dictionary mapping.** The keys are the input `parent_uuids` and values are lists of dictionaries containing the `_summary(org)` data.
- **Ordering is alphabetical.** Results are ordered by `Organization.name` to ensure deterministic UI rendering.

## Gotchas

- **Security scope enforcement:** Per commit `058aa8c`, this function is part of the tier-C cross-org scope enforcement logic. Ensure that the `join_model` and `fk_field` provided actually respect the intended visibility boundaries to avoid leaking OA data across organizations.
- **Dynamic attribute access:** Because `fk_col` is derived via `getattr(join_model, fk_field)`, passing an invalid string for `fk_field` will raise an `AttributeError` at runtime.

## Cross-cutting concerns

- **Auth**: Relies on the caller to ensure the `parent_uuids` provided are within the user's authorized scope.
- **Side effects**: Used by `GET::/api/series/{0}/races` (routers/series.py:287) to populate race-related organizational metadata.

## External consumers

- `GET::/api/series/{0}/races` (via import)
