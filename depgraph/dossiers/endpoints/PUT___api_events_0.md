---
node_id: PUT::/api/events/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1e61d34c652a8a9d4a9c050e92f60f2f6a7ba339c745218cf8f8c732e339bb73
status: llm_drafted
---

# PUT /api/events/{event_id}

## Purpose

Handles updates, deletions, and duplications for event resources. It provides the primary interface for modifying event metadata (like names, slugs, or categories) and managing the lifecycle of an event, including its associated regatta data. Use this endpoint when an admin or owner needs to modify an existing event's properties or create a clone of an event and its active tickets.

## Invariants

- **HTTP Method: `PUT`** for updates, **`DELETE`** for removal, and **`POST`** for duplication.
- **`owner_id` protection**: Non-admin users cannot change the `owner_id` of an event via the update payload.
- **Slug Uniqueness**: If a `slug` is provided in the update, the API validates that it is not already in use by another event (excluding the current `event_id`).
- **Category Validation**: The `category` field must exist within the `VALID_CATEGORIES` set.
- **Auth Requirement**: All operations require a valid `current_user` session via `require_auth`.

## Gotchas

- **Personal Event Slug Collision**: Per commit `4fd165d`, personal events must drop their slug or use a unique identifier to avoid global `UNIQUE` constraint collisions in the database.
- **Regatta Cascading Deletion**: Calling `DELETE` on an event with `category == "regatta"` will also delete the associated `Regly` record.
- **Permission Hierarchy**: While `personal` events have lighter restrictions, non-personal events require the `events.edit` permission or `org_admin`/`system_admin` roles to prevent unauthorized repurposing of organizational events.
- **Ownership Check**: The function `_require_can_modify_event` is a critical guard used across all three methods to ensure the user has the right to modify the specific event instance.

## Cross-cutting concerns

- **Auth**: Uses `require_auth`, `require_permission("events.delete")`, and `require_permission("events.create")`.
- **Side effects**: Updates to event data can affect the `schedule detail page` and the `schedule` view.
- **Audit**: Deletions of regatta-category events trigger a cascading delete of the linked `Regatta` record.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.update`
- `concorda-web::src/lib/api.ts::eventsApi.update`
