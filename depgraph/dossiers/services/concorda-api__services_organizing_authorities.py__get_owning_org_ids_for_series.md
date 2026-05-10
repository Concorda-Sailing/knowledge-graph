---
node_id: concorda-api::services/organizing_authorities.py::get_owning_org_ids_for_series
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b94619319ac274fdba3317c7163b5ce5d1f709168a347099d693e24a54583a2
status: current
---

# get_owning_org_ids_for_series

## Purpose

Retrieves the set of organization UUIDs that hold an "owning" relationship to a specific series. This is a critical scope-check helper used to determine which organizations have authority over a given series. It is distinct from `get_owning_org_ids_for_regatta`, which operates on the regatta level rather than the series level.

## Invariants

- **Returns a `set[str]`** containing organization UUIDs.
- **Filters by `OA_RELATIONSHIP`** — the query explicitly filters the `OrganizationSeries` table for the relationship type defined by this constant.
- **Input is a single `series_uuid`** (string).
- **Database dependency** — requires an active SQLAlchemy `Session` and the `OrganizationSeries` model.

## Gotchas

- **Tier-C security enforcement** — per commit `058aa8c`, this logic is part of the "tier-C cross-org scope enforcement" pattern. Changes to how this set is returned or filtered can directly impact cross-organization security boundaries.

## Cross-cutting concerns

- **Auth**: Used for tier-C scope enforcement to ensure users/orgs can only access resources they "own" or are authorized to view.
- **Side effects**: Affects the visibility of series-level data across the API.

## External consumers

None known.
