---
node_id: DELETE::/api/events/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 274a95513ec4101a35118dcc9be9d3c557f9c4fde3a36260fa76732cd3feb98b
status: llm_drafted
---

# DELETE /api/events/{event_id}

## Purpose

Deletes a specific event from the database. This endpoint is responsible for cleaning up both the primary `Event` record and any associated `Regatta` records if the event is categorized as a regatta. It is the standard way to remove an event from the system via the admin interface.

## Invariants

- **HTTP Method is `DELETE`** with a `204 No Content` success status.
- **Requires `events.delete` permission** via the `require_permission` guard.
- **Must pass `_require_can_modify_event`** to ensure the `current_user` has authority over the specific event instance.
- **Cascades to `Regatta`** — if `db_event.category == "regatta"`, the associated `Regatta` record is deleted before the event itself.
- **Returns 404** if the `event_id` does not exist in the database.

## Gotchas

- **Regatta dependency** — deleting an event with category `"regatta"` triggers a secondary deletion of the `Regatta` table entry. This is a hard-coded side effect in the router.
- **Slug collisions** — per commit `4fd165d`, personal events must handle slugs carefully to avoid global `UNIQUE` constraint violations; ensure any logic involving event creation/modification (which might precede a delete) respects the `drop slug for personal events` pattern.

## Cross-cutting concerns

- **Auth**: Requires `events.delete` permission via `require_permission("events.delete")`.
- **Side effects**: Deleting an event removes it from the schedule detail page and any calendar views where it was visible.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.delete` (via `adminEventsApi`)
