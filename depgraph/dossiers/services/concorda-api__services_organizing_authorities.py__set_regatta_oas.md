---
node_id: concorda-api::services/organizing_authorities.py::set_regatta_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 27dc14a0656ba919ba2b8e392dea2a1ed7d6d9ae03d0815b29d521491ce9bd46
status: current
---

# set_regatta_oas

## Purpose

Updates the association between a Regatta and its Organizing Authorities (OAs). It uses the `_set_oas` helper to synchronize the `OrganizationRegatta` join table, ensuring that the list of organizations with access to the regatta matches the provided `org_uuids`. This is a critical step in the regatta creation and update lifecycle to ensure proper multi-tenant scoping.

## Invariants

- **Uses `OrganizationRegatta` as the join model.** This distinguishes it from `set_event_oas` or `set_series_oas` which target different entity types.
- **Requires a `regatta_uuid` and an `Iterable[str]` of organization UUIDs.**
- **Mutates the database via `_set_oas`.** This involves deleting existing associations for the given `regatta_uuid` and inserting the new set of `org_uuids`.
- **Maintains the `regatta_uuid` as the foreign key.**

## Gotchas

- **Multi-OA transition:** Per commit `fdc87b4`, the system has moved toward supporting multiple Organizing Authorities for events and series. Ensure that any logic relying on a single-owner assumption is updated to handle the `set` of UUIDs returned by the sibling `get_owning_org_ids_for_regatta`.

## Cross-cutting concerns

- **Auth**: Indirectly affects scope enforcement; the resulting OAs determine which organizations can access the regatta resources.
- **Side effects**: Directly impacts the ability of organizations to see and manage the regatta via the `get_owning_org_ids_for_regatta` check used in API-level scope guards.

## External consumers

- `POST /api/regattas` (via `routers/regattas.py`)
- `PUT /api/regattas/{0}` (via `routers/regattas.py`)
