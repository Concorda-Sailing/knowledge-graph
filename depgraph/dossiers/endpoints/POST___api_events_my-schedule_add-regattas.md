---
node_id: POST::/api/events/my-schedule/add-regattas
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5d32a4313d9cb9cc9e512e1b6c6a5bca5ee18675c05c8a5a1860799b2e107e3f
status: llm_drafted
---

# POST /api/events/my-schedule/add-regattas

## Purpose

Adds regattas to a user's schedule by creating a `PersonEvent` (bookmark). It supports two modes: "Crew mode" (standard bookmarking) and "Captain mode" (triggered when `boat_uuid` is provided). In Captain mode, the endpoint also pre-populates a `SailingEvent` with default times and crew pool data. Use this endpoint when a user needs to both track a regatta and set up the operational details for their boat's participation.

## Invariants

- **Auth required** — Uses `require_auth` to identify the `current_user`.
- **Captain mode validation** — If `boat_uuid` is present, the user must pass the `_require_boat_owner` check for that specific boat.
- **Crew pool integrity** — If `crew_pool_id` is provided in Captain mode, the associated `CrewPool` must belong to the provided `boat_uuid`.
- **Role escalation** — If a user is already a "crew" member of an event, adding the regatta in Captain mode upgrades their `PersonEvent.role` to "captain".
- **Event creation** — Creates a shared `Event` with `category="regatta"` if one does not already exist for the given `regatta_id`.

## Gotchas

- **Role/Badge logic** — Per commit `8c29970`, the system is designed to suppress the "Crew" badge when a user is captaining their own boat for a race.
- **Date filtering** — Per commit `559491c`, the schedule logic (which consumes these events) floors filters at the start-of-today; ensure `regatta.start` is a valid datetime to avoid visibility issues.
- **Slug collisions** — Per commit `4fd165d`, personal events (created via this endpoint) use a specific slug pattern to avoid global `UNIQUE` constraint collisions in the `Event` table.
- **Role inheritance** — Per commit `7e6ed14`, this endpoint is responsible for recording the specific `captain` or `crew` role on the bookmark to ensure correct count-matching in the UI.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Side effects**: Updates the user's schedule; affects the "schedule detail page" and any view calculating "crew" vs "captain" counts for a regatta.

## External consumers

- `concorda-web`: `eventsApi.addRegattas` (via `api.ts:446`).
- `concorda-test`: `ApiClient.addRegattasToSchedule` (via `api-client.ts:278`).
