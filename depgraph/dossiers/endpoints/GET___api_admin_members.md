---
node_id: GET::/api/admin/members
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 04be09a99fa436b13497198a4cb4ad240b8ea16fca19ac21d87a3a81cf1e20da
status: llm_drafted
---

# GET /api/admin/members

## Purpose

Provides an administrative view of all members within an organization, supporting filtering by creation year, membership type (product slug), and text-based search. It is the primary endpoint for populating the admin-side member grid. Use this instead of the `/stats` endpoint when you need granular person-level data rather than aggregate counts.

## Invariants

- **Requires `org_admin` or `system_admin` roles** via the `_require_admin` dependency.
- **Returns a paginated object** containing `total` (count), `skip`, `limit`, and a `members` list.
- **`limit` is capped** between 1 and 100.
- **Search is case-insensitive** and uses ILIKE patterns for `first_name`, `last_name`, and `email`.
- **Membership filtering** requires a join through `PersonProduct` and `TemporalProduct` to match the `slug`.

## Gotchas

- **Role escalation risk:** Per commit `650233f`, ensure any changes to the dependency logic do not inadvertently bypass the `_require_admin` check, as this endpoint exposes sensitive PII (email, names).
- **Pagination/Offset behavior:** The `skip` and `limit` parameters are used for offset-based pagination; ensure the frontend handles the `total` count correctly to prevent UI drift.
- **Join complexity:** Filtering by `membership_type` performs a join on `TemporalProduct`. If the `membership_type` string does not match a valid `TemporalProduct.slug`, the query returns an empty list rather than an error.

## Cross-cutting concerns

- **Auth**: Strictly guarded by `_require_admin` (requires `org_admin` or `system_admin`).
- **Rate limit**: None explicitly defined for this endpoint, but subject to general API rate-limiting policies.
- **Audit**: N/A.

## External consumers

None known.

## Open questions

- The `year` filter uses `extract("year", Person.created)`. If we move to a more complex temporal model for membership history, this filter may need to be updated to check `leave_date` instead.
