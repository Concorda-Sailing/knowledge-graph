---
node_id: concorda-web::src/lib/api.ts::eventsApi.register
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 753080e1e3786ade8b97f7303c736c744861b751bfacab52b9ea516568db3ea4
status: current
---

# eventsApi.register

## Purpose

Handles the registration of users for specific events and the management of their personal schedules. It provides two distinct paths for registration: `register` (unauthenticated/public-facing via `fetchApi`) and `registerAuthenticated` (authenticated via `fetchApiAuthenticated`). Use `register` for public landing pages and `registerAuthenticated` for user-facing dashboard actions.

## Invariants

- **`register` uses `fetchApi`** — This is the public endpoint for event registration and does not require a bearer token.
- **`registerAuthenticated` uses `fetchApiAuthenticated`** — All schedule-modifying methods (add/remove/update) require an active session.
- **`register` returns `EventRegistrationResponse`** — The response shape is critical for confirming successful sign-ups on the UI.
- **Time formats for `addRegattas` and `addSeries`** — `dock_time` and `departure_time` must be provided in `"HH:MM"` 24h format.

## Gotchas

- **`departure_time` default logic** — Per the source, `departure_time` defaults to `dock_time + 45m` on the client side; ensure any manual overrides match the expected `"HH:MM"` string format to avoid API rejection.
- **`mySchedule` coupling** — Per commit `1b5d864`, the detail page was refactored to call `/api/events/{id}/detail` specifically to drop the coupling to the `mySchedule` endpoint, preventing unnecessary data fetching when viewing event details.
- **`boat_uuid` vs. `crew_pool_id`** — When calling `addSeries`, omitting `boat_uuid` acts as a "bookmark as crew" action, which is a distinct mode from registering as a boat/owner.

## Cross-cutting concerns

- **Auth**: `register` is public; all other methods (`registerAuthenticated`, `update`, `addRegattas`, `addSeries`, `addEvents`, `removeScheduleEvent`, `removeScheduleSeries`) require `fetchApiAuthenticated`.
- **Side effects**: Updates to these endpoints trigger changes in the "my schedule" view and the "accepting-crew" status on regatta detail pages.

## External consumers

None known.

## Open questions

- Is there a need for a specialized `registerAsCrew` helper to explicitly handle the `boat_uuid: null` case, or is the current optionality in `addSeries` sufficient?
