---
node_id: POST::/api/events/my-schedule/add-series
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: da1c25dc9fc358356be04cd188becdd461932598ace8121fbcb4abc8cf359ae1
status: current
---

# POST /api/events/my-schedule/add-series

## Purpose

Adds every race in a specific series to the current user's schedule. It serves two distinct modes: a "crew" mode (plain bookmarking) and a "captain" mode (triggered by providing a `boat_uuid`). In captain mode, the endpoint also pre-populates `SailingEvent` data (dock time, departure, duration, and crew pool) so the user doesn't have to manually configure each race.

## Invariants

- **POST** to `/api/my-schedule/add-series`.
- **Requires `series_uuid`** to identify the set of regattas.
- **Captain Mode Check**: If `boat_uuid` is provided, the user must be the owner of that boat via `_require_boat_owner`.
- **Crew Pool Validation**: If `crew_pool_id` is provided in captain mode, it must belong to the specified `boat_uuid`.
- **Role Assignment**: Sets the `PersonEvent.relationship` to `"schedule"`. If a user is already a "crew" member for an event, adding the series as a captain upgrades their role to `"captain"`.
- **Idempotency (Partial)**: Does not create duplicate `PersonEvent` entries if the user is already bookmarked for a specific event.

## Gotchas

- **Role Upgrades**: Per commit `7e6ed14`, the logic explicitly checks if an `existing_bookmark.role != "captain"` before upgrading to ensure a user can transition from crew to captain for a series.
- **Captain Mode Defaults**: In captain mode, `dock_time` and `departure_time` are parsed via `_parse_hhmm`. If these are not provided, the `SailingEvent` creation logic relies on the fallback behavior defined in the model/parser.
- **Series/Event Disconnect**: If the `series_uuid` does not resolve to any `Regatta` objects, the API returns a `404`.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Audit**: N/A.
- **Side effects**: Triggers creation of `PersonEvent` (bookmarks) and potentially `SailingEvent` (if in captain mode) which updates the user's schedule view.

## External consumers

- `concorda-web` (via `eventsApi.addSeries`)
