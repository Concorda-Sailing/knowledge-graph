---
node_id: concorda-api::services/organizing_authorities.py::get_event_oas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e219380c9f1d2e28f3529782833c2cefcc203c0dd0aefebf9ee00c036fe7d03d
status: current
---

# get_event_oas

## Purpose

Retrieves the list of Organizing Authorities (OAs) associated with a specific event. It uses the `OrganizationEvent` join model to identify which organizations have a defined relationship with the event. This is a read-only helper used to determine organizational scope for an event.

## Invariants

- **Returns a list of dictionaries.** Each dictionary represents an organization summary.
- **Requires a valid `event_uuid`.** The function relies on this UUID to filter the `OrganizationEvent` join table.
- **Relationship is fixed to `OA_RELATIONSHIP`.** The query specifically filters for the `organizing_authority` relationship type.
- **Dependency on `_get_oas`.** This method is a thin wrapper around the internal `_get_oas` utility which handles the core database query logic.

## Gotchas

- **Multi-OA support vs. Legacy.** Per commit `fdc87b4`, the system now supports multi-OA events. However, `get_owning_org_ids_for_event` (a sibling) still checks the legacy `Event.organizing_club_id` to ensure backward compatibility for events that haven't migrated fully to the join-table model.
- **Scope enforcement.** Per commit `058aa8c`, this data is critical for tier-C cross-org scope enforcement; ensuring the correct OAs are returned is vital for preventing unauthorized access to event data.

## Cross-cutting concerns

- **Auth**: Used for tier-C cross-org scope enforcement (see commit `058aa8c`).
- **Side effects**: Used by the event duplication flow (see `POST /api/events/{0}/duplicate`) to determine which organizations should inherit ownership/authority during a clone.

## External consumers

- `POST /api/events/{0}/duplicate` (via `routers/events.py`).
