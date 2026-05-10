---
node_id: concorda-web::src/components/boat/boat-photos.tsx::BoatPhotos
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0f21d248956c14e7fb52ab3de258c7625e5cde1b691c52df997c0ddb77ead8e6
status: llm_drafted
---

# BoatPhotos

## Purpose

The `BoatPhotos` component manages the visual media assets for a specific boat. It provides interfaces for browsing photos, organizing them into albums (folders), and uploading new images. It distinguishes between a general "all photos" view and specific album views, allowing users to manage media tied to specific events or general boat history.

## Invariants

- **Entity Type is Fixed** — All `mediaApi` calls (listing, uploading) must use `entity_type: "boat"` and `entity_uuid: boatId`.
- **Upload Scope** — Uploaded files are assigned a `scope: "crew"` by default.
- **Image Validation** — The upload loop explicitly checks `!file.type.startsWith("image/")` to prevent non-image file uploads.
- **Album/Folder Relationship** — When uploading to an album, the `folder_uuid` is passed to the `mediaApi.upload` method; if no album is selected, it is passed as `undefined`.

## Gotchas

- **Mobile Full-screen Bug** — Per commit `93bbf6d`, the photos lightbox/viewer has issues with full-screen rendering on medium-sized screens (`<md`). Ensure any changes to the lightbox or image rendering logic do not break the mobile-responsive full-screen state.
- **Duplicate Handling** — The component catches errors where `err.message.includes("already been uploaded")`. This is a known behavior of the `mediaApi.upload` endpoint to prevent redundant storage usage.
- **Timezone Rendering** — Per commit `f444b4c`, any datetime-related metadata displayed for photos (e.g., when a photo was taken) must be rendered in the organization's timezone, not the browser's local time.

## Cross-cutting concerns

- **Auth**: Uses `mediaApi` which requires an authenticated session; `isOwner` prop determines UI visibility for certain management actions.
- **Side effects**: Changes to photo/album state may affect the visual representation of the boat's history in the `BoatProfileTab`.

## External consumers

None known.
