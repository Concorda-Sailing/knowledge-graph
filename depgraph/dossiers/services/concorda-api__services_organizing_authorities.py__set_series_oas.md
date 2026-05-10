---
node_id: concorda-api::services/organizing_authorities.py::set_series_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8867c981880e9029923017cb91d41a01a97253fde7a360f708800143c029ac4e
status: current
---

# set_series_oas

## Purpose

Updates the list of Organizing Authorities (OAs) associated with a specific `OrganizationSeries`. It uses the internal `_set_oas` helper to synchronize the `OrganizationSeries` join table with the provided `org_uuids`. Use this method when a series' ownership or management structure changes to ensure the database reflects the current set of authorized organizations.

## Invariants

- **Mutates `OrganizationSeries` join table** — replaces existing associations for the given `series_uuid`.
- **Requires a valid `series_uuid`** — the parent identifier for the series being updated.
- **Input is an `Iterable[str]`** — accepts a list or set of organization UUIDs to be associated with the series.
- **Uses `_set_oas` for synchronization** — relies on the underlying implementation to handle the deletion of old associations and insertion of new ones.

## Gotchas

- **Security context is critical** — per commit `058aa8c` (`security: tier-C cross-org scope enforcement`), this method is a core part of the multi-OA ownership model. Changes to how OAs are assigned here directly impact the scope of data visibility and access control for series-level resources.
- **Directly affects series-level ownership** — because this method modifies the `OrganizationSeries` relationship, it is a primary driver for the "multi-OA" logic described in the `get_owning_org_ids_for_series` logic.

## Cross-cutting concerns

- **Auth**: Directly impacts tier-C cross-org scope enforcement (see commit `058aa8c`).
- **Side effects**: Updates the ownership set for any `Product` or `Event` that relies on `get_owning_org_ids_for_series` for access control.

## External consumers

- `POST /api/series` (via `routers/series.py:160`)
- `PUT /api/series/{0}` (via `routers/series.py:185`)
