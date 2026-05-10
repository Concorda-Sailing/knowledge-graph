---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.uploadImage
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2767e3c5959a58b81c26462ba59f7222687c27dcc75998bea43a08606c1f0bc4
status: current
---

# adminEventsApi.uploadImage

## Purpose

Handles the multipart/form-data upload of an image file to a specific event. It is distinct from `deleteImage` (which removes the asset) and `update` (which modifies event metadata). Use this method when a user is uploading a cover photo or event-specific media via the admin event detail view.

## Invariants

- **Input is a `File` object.** The second argument must be a browser `File` instance to ensure correct multipart encoding.
- **Returns an `Event` object.** The response body is the updated event state, allowing the UI to immediately reflect the new image URL.
- **Targets a specific event ID.** The endpoint is `/api/events/${id}/image`.

## Gotchas

- **Uses `fetchApiUpload` instead of `fetchApiAuthenticated`.** Unlike the standard `update` or `delete` methods in the same service, this uses a specialized wrapper to handle the `FormData` and multipart boundaries correctly.
- **Direct dependency of `EventDetailContent`.** Two specific call sites in `concorda-web/src/app/members/admin/events/[id]/page.tsx` (at `page.tsx:465` and `page.tsx:553`) rely on this for the admin event management interface.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiUpload` which relies on the authenticated session/token.
- **Side effects**: Successful uploads update the event object, which is used to refresh the event detail view in the admin dashboard.

## External consumers

None known.
