---
node_id: GET::/api/crewfinder
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 583b41249fb6aaa63dbfb90917bf610dc9002c9e896e6c368583ed4d12104a68
status: current
---

# GET /api/crewfinder

## Purpose

Provides a list of profiles for sailors who have opted-in to the "Crew Finder" feature. It allows boat owners and members to discover available crew based on experience level, preferred positions, and race areas. This is distinct from the standard directory or person lookup, as it strictly filters for users who have explicitly enabled visibility via their `preferences`.

## Invariants

- **Requires `crewfinder.view` permission** via the `require_permission` dependency.
- **Filters by `opt_in` status** using a JSON extract on `Person.preferences` to ensure only opted-in users are returned.
- **Redacts PII by default** — `email` and `phone_number` are only included in the `CrewfinderProfile` if the user's specific preference (`show_email` or `show_phone`) is set to true.
- **Returns a list of `CrewfinderProfile` objects** containing a subset of `SailingResume` and `Person` data.
- **Ordering is deterministic** by `Person.last_name` and `Person.first_name`.

## Gotchas

- **Security/PII Leakage:** Per commit `33a37a3`, this endpoint was specifically hardened to close PII/privilege gaps. Ensure that any future additions to the `CrewfinderProfile` schema do not inadvertently expose sensitive fields (like raw email/phone) without checking the `prefs.get("show_email")` logic.
- **Permission Logic:** The filter `not_(func.json_extract(Person.disabled_permissions, "$").like('%crewfinder.view%'))` is critical. If a user has a disabled permission for this view, they are excluded from the results even if they have opted into the crew finder.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `crewfinder.view` permission.
- **Side effects**: Changes to a user's `preferences` (specifically `crewfinder.opt_in`, `show_email`, or `show_phone`) immediately change their visibility and data exposure in this list.

## External consumers

None known.

## Open questions

- The `get_crew_detail` endpoint (the `/detail/{person_id}` sibling) provides more depth; it is unclear if the list view should eventually include a "preview" of the detail-level data or if the current separation is intentional for performance.
