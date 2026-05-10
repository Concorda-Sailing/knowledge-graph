---
node_id: GET::/api/merchandise
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bcf5c6e23a087bd306e684aea0c0cd18443c8c61c2c19ab366a6532e0f80156c
status: llm_drafted
---

# GET /api/merchandise

## Purpose

Provides a list of all merchandise items available in the system. This endpoint is used by administrative interfaces to display the current inventory. It is distinct from the specific item retrieval endpoint (`GET /api/merchandise/{item_id}`) which targets a single record.

## Invariants

- **Requires `admin.memberships.view` permission** via the `require_permission` dependency.
- **Returns a list of `MerchandiseRead` objects.**
- **Supports an `include_inactive` query parameter.** By default, this is `false`, meaning the response only includes items where `is_active == True`.
- **Orders by `sort_order`.** The list is automatically sorted by the `Merchandise.sort_order` field.

## Gotchas

- **Implicit filtering.** If a user sees a missing item that they expect to be present, check if `is_active` is false; the endpoint defaults to hiding inactive items unless `include_inactive=True` is explicitly passed.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.view` permission.
- **Rate limit**: none.
- **Side effects**: none.

## External consumers

None known.
