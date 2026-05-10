---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.deleteImage
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 75655aa10e4f5b1567ab0fcb294a20e6eecbdb3c85d2f7445d93f892e6af1c62
status: llm_drafted
---

# adminEventsApi.deleteImage

## Purpose

Removes an image associated with a specific event. It targets the `/api/events/${id}/image` endpoint using a `DELETE` method. This is distinct from `delete` (which removes the entire event) or `uploadImage` (which replaces/adds the image); this method is specifically for clearing the image asset.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `fetchApiAuthenticated`** — the request must include a valid bearer token.
- **Returns `Event` (or `void` implicitly via the `Event` type generic)** — the response shape is handled by the underlying fetch wrapper.
- **Target path is `/api/events/${id}/image`**.

## Gotchas

- **Dependency on `EventDetailContent`** — the UI component in `src/app/members/admin/events/[id]/page.tsx` relies on this to clear images. If the image removal fails, the UI may still attempt to render a broken image link or a stale asset.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Deleting the image affects the visual state of the event detail page.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (EventDetailContent)
