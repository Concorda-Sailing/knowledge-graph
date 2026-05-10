---
node_id: DELETE::/api/events/my-schedule/events/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 572838ba2c45589c785d29e13f7e09343b6c7944fd8667fd6ffcffc4ee3a179b
status: current
---

# DELETE /api/events/my-schedule/events/{event_id}

## Purpose

Removes an event from a user's personal schedule. The method handles three distinct scenarios: removing a simple bookmark (`PersonEvent`), removing a personal event copy (where the user is the owner), or removing a co-owner relationship where the user is an active owner of a boat involved in the event. It is designed to ensure that when a user "untracks" an event, any dependent data (like `EventCrew` records or the `SailingEvent` itself) is cleaned up to prevent orphaned records.

## Invariants

- **HTTP Method:** `DELETE`.
- **Auth:** Requires `require_auth` via the `current_user` dependency.
- **Return Shape:** Returns an object containing `removed` (boolean), `had_plan` (boolean), and `crew_removed` (boolean).
- **Cleanup Logic:** Uses `_cleanup_sailing_event` to handle cascading deletions of dependent records.
- **Atomicity:** Uses `db.commit()` after identifying the specific type of removal (bookmark, personal, or co-owner) to ensure the state change is finalized.

## Gotchas

- **Co-owner cleanup requires explicit flush:** Because the session uses `autoflush=False`, a manual `db.flush()` is required after calling `_cleanup_sailing_event` to ensure the `SailingEvent` deletion is visible to subsequent checks in the same request.
- **Personal event visibility:** Per commit `57f2e00`, the logic must ensure user-owned personal events are always included/accessible regardless of date-based filters to avoid "disappearing" events during the removal flow.
- **Slug collisions:** Per commit `4fd165d`, the system uses a specific pattern for personal events to avoid global `UNIQUE` collisions on event slugs.

## Cross-cutting concerns

- **Auth**: Requires `current_user` (authenticated user).
- **Side effects**: Triggers cleanup of `EventCrew` and `SailingEvent` records, which may affect the visibility of boat/event status in the schedule.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.removeScheduleEvent`
- `concorda-web::src/lib/api.ts::eventsApi.removeScheduleEvent`
