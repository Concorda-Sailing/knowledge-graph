---
node_id: DELETE::/api/events/{0}/image
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3ccb437f2df6745d9d9bcf6fc3d321cac45aee07aad44b97b858609c8bdb4aaa
status: current
---

# DELETE /api/events/{event_id}/image

## Purpose

Removes the event image from both the storage provider and the database record. This is the inverse of the upload flow and is used when an event organizer wants to clear or reset the event's visual branding.

## Invariants

- **HTTP Method is `DELETE`** — used to signal the removal of the resource.
- **Requires `events.edit` permission** — enforced via `require_permission("events.edit")`.
- **Returns the updated `Event` object** — the response body is the `EventRead` model with `image_url` set to `null`.
- **Clears the database field** — sets `db_event.image_url = None` before committing.

## Gotchas

- **Permission check is two-tiered** — first requires the `events.edit` permission, then calls `_require_can_modify_event` to ensure the user has ownership/authority over the specific event instance.
- **Orphaned files** — the `delete_upload("events", event_id)` call is responsible for the physical file removal. If this fails or is bypassed, the storage remains cluttered.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Side effects**: The `image_url` becomes `null`, which may affect how the event is rendered in the schedule detail page or event list views.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.deleteImage`
