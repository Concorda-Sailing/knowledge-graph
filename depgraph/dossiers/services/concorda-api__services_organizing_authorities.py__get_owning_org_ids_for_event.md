---
node_id: concorda-api::services/organizing_authorities.py::get_owning_org_ids_for_event
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 499752acdafd769add04f0aa26c9ed5e3fb3ab25f9cebe11ff049e53f97e15f2
status: current
---

# get_owning_org_ids_for_event

## Purpose

Retrieves the set of organization UUIDs that own a specific event, used primarily for multi-tenant scope enforcement. It aggregates ownership from two sources: the modern `OrganizationEvent` many-to-many relationship (using `OA_RELATIONSHIP`) and the legacy `Event.organizing_club_id` column. This ensures that even during the transition from single-org to multi-org event structures, access control remains intact.

## Invariants

- **Returns a `set[str]`** — even if no ownership is found, it returns an empty set, never `None`.
- **Combines legacy and modern schemas** — it must check both the `OrganizationEvent` join table and the `Event.organizing_club_id` field to ensure consistent permissioning.
- **Uses `OA_RELATIONSHIP`** — the filter on the join table is hardcoded to this constant to ensure only "organizing authority" relationships are counted, not other types of associations.

## Gotchas

- **Legacy field fallback is critical** — per commit `fdc87b4`, the transition to multi-OA events requires checking `Event.organizing_club_id`. If this check is removed, events created under the old schema will appear to have no owners, potentially breaking tier-C security boundaries.
- **Empty set vs. None** — if an event is "personal" (no organization assigned), the function returns an empty set. Callers must handle the empty set as "no organizational ownership" rather than assuming a database error.

## Cross-cutting concerns

- **Auth**: Directly used for tier-C cross-org scope enforcement (see commit `058aa8c`).
- **Audit**: N/A.
- **Side effects**: Affects the visibility of events in list endpoints and permission checks for any resource (Regatta, Series, or Product) that derives its ownership from an Event.

## External consumers

None known.
