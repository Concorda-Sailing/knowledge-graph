---
node_id: concorda-web::src/lib/api.ts::eventsApi.suggestCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fdb64807972a2ca1d25f4434043c704ade4cafc1e988641363d1da32ae9b9f7
status: current
---

# eventsApi.suggestCrewPool

## Purpose

Fetches the list of available crew members (UUIDs) for a specific event. This is used to populate the "suggested crew" UI, allowing organizers to see potential candidates for open positions. It is distinct from `confirmEventCrew` or `requestToCrew` as it is a read-only operation that returns a list of strings rather than modifying membership or state.

## Invariants

- **Returns `string[]`** — The response is a simple array of user UUID strings.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the caller has a valid session.
- **Path structure** — Follows the pattern `/api/events/${eventId}/sailing-event/crew-suggest`.

## Gotchas

- **Display logic dependency** — Per commit `2d6b8a7`, the results from this call are used to drive the "accepting-crew" status on regatta detail pages and the config-aware count on schedule cards.
- **UI/UX coupling** — As noted in commit `bf44b09`, this is part of the logic for handling the `EventCrewStatus` type union and the schedule-card pool handling.

## Cross-cutting concerns

- **Auth**: `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Drives the "accepting-crew" status badge on the regatta detail view and the count displayed on the schedule card.

## External consumers

None known.
