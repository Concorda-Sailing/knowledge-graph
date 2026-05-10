---
node_id: GET::/api/events/{0}/sailing-event/crew-suggest
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52b98920b2108dfd1c4d5b1173271a6b92c40c45ea9de126a97a053702e24f70
status: current
---

# GET /api/events/{event_id}/sailing-event/crew-suggest

## Purpose

Provides a list of suggested crew members for a specific sailing event by looking at historical data. It identifies a "best" candidate event by prioritizing the most recent event within the same series, falling back to any recent event involving the same boat. This is used to surface a pool of likely crew members to reduce manual entry during event creation.

## Invariants

- **Requires `owner` relationship** — The `current_user` must be the owner of the sailing event via `_get_user_sailing_event_or_404`.
- **Returns a list of strings** — The response model is `list[str]`, specifically the `person_uuid` of the crew members.
- **Filters by status** — Only returns crew members whose status is either `"accepted"` or `"confirmed"`.
- **Strictly limited to 20 candidates** — The search for the source event is limited to the 20 most recent `SailingEvent` entries for the boat.

## Gotchas

- **Series priority logic** — The function implements a two-tier search: it first attempts to find a candidate within the same `series_event` relationship, then falls back to any recent event with a crew.
- **Empty results on no matches** — If no suitable candidate event is found, it returns an empty list `[]` rather than a 404 or error.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and verifies the user is the owner of the event.
- **Side effects**: Indirectly related to the "Crew badge" logic; see commit `8842b8d` regarding suppressing the badge when captaining one's own boat.

## External consumers

- `concorda-web` (via `eventsApi.suggestCrewPool`)
