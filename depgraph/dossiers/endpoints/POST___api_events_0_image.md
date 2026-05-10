---
node_id: POST::/api/events/{0}/image
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 874cfcd2bf2dccc6a3f3c872e9f7306d8f9d2cc882a9c1c4da58ab3e62431422
status: current
---

# POST /api/events/{event_id}/image

## Purpose

Handles the uploading and storage of a single image for a specific event. It manages the lifecycle of the event's visual asset by saving the file to the `events` storage bucket and updating the `image_url` field on the `Event` model. Use this endpoint when a user needs to set or change the primary visual representation of an event.

## Invariants

- **Requires `events.edit` permission** via the `require_permission("events.edit")` dependency.
- **Input is a single file** via `UploadFile` and must be sent as a multipart/form-data body.
- **Enforces a `max_dimension=1200`** during the `save_upload` call to prevent excessive storage/bandwidth usage.
- **Updates the `db_event.image_url` field** directly, replacing any existing URL.
- **Returns the full `EventRead` object** upon successful upload, allowing the client to immediately access the new `image_url`.

## Gotchas

- **Permission check is strict.** The `current_user` must pass the `require_permission("events.edit")` check and the internal `_require_can_modify_event` check.
- **File storage path is fixed.** The `save_upload` function uses the `"events"` prefix and the `event_id` to organize files; changing this logic will break the link between the DB record and the physical file.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Side effects**: Updating the image URL affects any UI component that renders the event header or event card (e.g., the schedule detail page).

## External consumers

None known.
