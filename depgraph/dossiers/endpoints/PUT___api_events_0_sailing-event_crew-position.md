---
node_id: PUT::/api/events/{0}/sailing-event/crew-position
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1566421115904d90a9ccf23860d464dc05f5bf636c2cfc7a2d837be6f19dd636
status: current
---

# PUT /api/events/{event_id}/sailing-event/crew-position

## Purpose

Allows a user who is already an accepted/confirmed crew member to set or change their specific position within a sailing event. This is distinct from the `crew-pool` endpoint, as it is restricted to users who already have a valid relationship with the event. It also serves a dual purpose of updating the user's `SailingResume` by appending the new position to their `positions_preferred` list.

## Invariants

- **Requires `require_auth`** — The user must be authenticated.
- **Relationship check** — The user must be a member of the event (via `_get_user_sailing_event_or_404` with `relation="crew"`) or the request fails with 404.
- **Status requirement** — The user's current status in the event must be either `"accepted"` or `"confirmed"`.
- **Position validation** — If a `position_name` is provided, it must exist within the `se.positions_needed` list of the event.
- **Capacity check** — The request fails with 400 if the requested position's `taken_count` has reached its defined `pos_count`.
- **Returns `EventCrewRead`** — The response contains the updated crew record.

## Gotchas

- **Side effect on `SailingResume`** — Updating a position here mutates the user's global `SailingResume.positions_preferred`. This is a side effect that is not immediately obvious from the endpoint name.
- **Race condition on position capacity** — The check for `taken_count` happens in-memory before the commit. High-frequency updates to the same position could theoretically bypass the `pos_count` limit if multiple requests hit simultaneously.
- **`self_selected = True`** — Setting a position via this endpoint automatically flags the record as `self_selected`.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the `current_user` is the one making the change.
- **Websocket**: Calls `broadcast_event(EVENT_CREW_UPDATED, se.id)` upon successful commit, which triggers UI updates for event participants.
- **Side effects**: Updates the user's `SailingResume` (specifically `positions_preferred`).

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.updateMyPosition`
