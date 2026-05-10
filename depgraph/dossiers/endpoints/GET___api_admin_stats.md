---
node_id: GET::/api/admin/stats
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 44f1486d0883358c4e4308f01182b427459893a646a4a7abbfffe52a27dc8c4b
status: current
---

# GET /api/admin/stats

## Purpose

Provides high-level aggregate statistics for the administrative dashboard. It calculates counts for members, clubs, events, and regattas, alongside a breakdown of membership types. This is the primary source for the "at-a-glance" overview of the organization's scale and activity.

## Invariants

- **Returns a single JSON object** containing integer counts for `total_members`, `active_members`, `total_clubs`, `upcoming_events`, `upcoming_regattas`, and `crewfinder_profiles`.
- **`membership_by_type` is a dictionary** where keys are `TemporalProduct.name` and values are counts.
- **Uses UTC-aware comparisons** for `upcoming_events` and `upcoming_regattas` via `datetime.now(timezone.utc)`.
- **`crewfinder_profiles` relies on JSON extraction** from the `Person.preferences` field to identify opt-in status.

## Gotchas

- **Security sensitivity:** Per commit `650233f`, admin endpoints are subject to strict privilege checks; ensure any changes to this endpoint do not inadvertently expose sensitive user data or bypass the `block privilege escalation` logic.
- **Database load:** The endpoint performs multiple heavy aggregate queries (count, join, group_by) across `Person`, `Organization`, `Event`, `Regatta`, and `TemporalProduct`. Frequent polling may impact DB performance.

## Cross-cutting concerns

- **Auth**: Requires admin-level privileges (implied by the `/api/admin/` path and recent security-hardening commits).
- **Side effects**: The data returned here populates the primary metrics on the Admin Dashboard.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.stats` (The primary consumer for the admin dashboard).

## Open questions

- The `crewfinder_profiles` count relies on a `func.json_extract` on a JSON field; if the schema for `Person.preferences` changes or the field is moved, this count will silently return 0 or fail. Should this be moved to a formal boolean column for better performance and reliability?
