---
node_id: GET::/api/events/personal
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 94a3dc6b1b0c42c97a1c5ccef1950b006ade1ce97026e54dc1a6bb52ae83c678
status: llm_drafted
---

# GET /api/events/personal

## Purpose

Retrieves a list of "personal" events belonging to the authenticated user. This endpoint is distinct from the core `list_events` or `list_upcoming_events` routes, which explicitly filter out the `personal` category to prevent cluttering global/regional views. Use this when the UI needs to display a user-specific schedule or private entries that should not be visible to the broader organization.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Filters by `category == "personal"`** and matches the `owner_id` to the `current_user.id`.
- **Returns a list of `EventRead` objects**, which is a subset of the more complex `EventReadWithRegatta` used in core endpoints.
- **Orders results by `Event.date`** in ascending order.

## Gotchas

- **Category exclusion logic is strict.** The core `list_events` and `list_upcoming_events` endpoints explicitly filter out `category != "personal"` by default. If a user expects to see their personal events in a global feed, they will not appear here unless the category is changed.
- **Slug collision risk.** Per commit `4fd165d`, personal events must avoid using slugs that could collide with global unique constraints.
- **Date filtering sensitivity.** Per commit `57f2e00` and its revert, there was a regression regarding whether user-owned personal events should be included regardless of date; ensure that any client-side filtering logic respects that these are intended for a "personal" view rather than a global chronological view.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to populate `current_user`.
- **Side effects**: Used to populate user-specific schedule views and private event lists.

## External consumers

None known.
