---
node_id: GET::/api/admin/delegates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c0d927c9727e2adb88583241ca199f68940d86aeb96bfc93b3f5ca405c6dbd66
status: current
---

# GET /api/admin/delegates

## Purpose

Provides a list of all organizations categorized as "Yacht Club" along with their associated delegate (steward) information. This is used by administrative interfaces to map high-level organizational entities to specific human contacts. It is distinct from the general organization list as it specifically filters for the `Yacht Club` `org_type` to isolate primary stakeholders.

## Invariants

- **Filters by `Organization.org_type == "Yacht Club"`** — only organizations with this specific type are returned.
- **Returns a list of objects** containing a `club` (Organization object) and a `delegate` (Person object or null).
- **Orders by `Organization.name`** — the list is sorted alphabetically by the club name.
- **`delegate` is nullable** — if `club.steward_id` is null or the person does not exist, the `delegate` field returns `null`.

## Gotchas

- **Dependency on `steward_id`** — the link between a club and its delegate is driven by the `steward_id` field on the `Organization` model. If the relationship is broken or the ID is incorrect, the delegate will return as `null` without an error.
- **Potential for N+1 queries** — the implementation performs a `db.query(Person)` inside a loop for every club found. While acceptable for small admin lists, this will scale poorly if the number of Yacht Clubs grows significantly.

## Cross-cutting concerns

- **Auth**: None explicitly required by the function signature, but resides under the `/api/admin` router which is typically protected by higher-level admin middleware.
- **Side effects**: Used by `adminApi.delegates` in the web frontend to populate administrative contact lists.

## External consumers

- concorda-web (via `adminApi.delegates`)
