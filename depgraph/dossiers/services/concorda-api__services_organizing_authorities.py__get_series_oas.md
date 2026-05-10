---
node_id: concorda-api::services/organizing_authorities.py::get_series_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 93e16476d601e6410493f0a8b9f60359308513c2436ee729aef6d68dacb2c5e9
status: llm_drafted
---

# get_series_oas

## Purpose

Retrieves the list of Organizing Authorities (OAs) associated with a specific series via the `OrganizationSeries` join model. This is a specialized getter used to determine which organizations have administrative or ownership visibility over a series, distinct from the regatta-level or event-level lookups.

## Invariants

- **Returns a list of dictionaries.** Each dictionary represents an organization-series relationship.
- **Requires a `series_uuid` and a valid SQLAlchemy `Session`.**
- **Uses `OrganizationSeries` as the join model.** It specifically filters by the `series_uuid` field to find associated organizations.

## Gotchas

- **Multi-OA support is a recent change.** Per commit `fdc87b4`, the system has moved toward supporting multiple Organizing Authorities for series (and events) to allow for more complex ownership models. Ensure any logic relying on a single-owner assumption is updated to handle the list returned here.

## Cross-cutting concerns

- **Auth**: Used for scope enforcement; determines which organizations can see or modify series-level data.
- **Side effects**: Directly used by `POST /api/series/{0}/generate-races` (via `routers/series.py:217`) to validate permissions before race generation.

## External consumers

- `POST /api/series/{0}/generate-races` (via `routers/series.py`)
