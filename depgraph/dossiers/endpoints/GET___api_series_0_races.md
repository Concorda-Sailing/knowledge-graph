---
node_id: GET::/api/series/{0}/races
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1c2c356a29597b7ed9e9272d992368cdc020d03ee9c8373c8e3ce39a6d6e2fce
status: llm_drafted
---

# GET /api/series/{series_id}/races

## Purpose

Retrieves all regattas (races) associated with a specific series, including their associated Organizing Authorities (OAs). This endpoint is used to populate the schedule view for a series. It is distinct from the base `GET /api/series/{series_id}` endpoint because it performs a bulk lookup of `organizing_authorities` via `get_oas_bulk` to ensure the UI can display which organizations are hosting each race in the list.

## Invariants

- **Returns a list of objects** following the `RegattaRead` schema, augmented with an `organizing_authorities` key.
- **Ordering is strictly by `Regatta.start`** to ensure the chronological sequence of the series is preserved in the UI.
- **Returns a 404 error** if the `series_id` does not exist in the database.
- **`organizing_authorities` is a list of objects**, populated via the `get_oas_bulk` helper and the `OrganizationRegatta` join model.

## Gotchas

- **Complexity of the return shape**: Unlike a standard regatta fetch, this endpoint manually injects `organizing_authorities` into the dictionary after validation. If the `RegattaRead` schema is modified to include this field, the manual injection in `d["organizing_authorities"] = ...` may become redundant or cause type-mismatch warnings in the service layer.
- **Performance of bulk lookups**: The endpoint performs a `get_oas_bulk` call. As seen in the recent history of `fdc87b4` (feat: events multi-OA), the system now supports multiple Organizing Authorities per event; ensure that the `join_model` and `fk_field` logic remains compatible with this multi-OA expansion.

## Cross-cutting concerns

- **Auth**: None (Public/Read-only access to series structure).
- **Side effects**: Used by the series schedule view to display the chronological list of regattas and their hosting organizations.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.listRaces`
