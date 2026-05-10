---
node_id: concorda-web::src/app/members/admin/files/page.tsx::AdminFilesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6117b98c99d608c165b049a3a328b822ff157a2e2669e8d5df938d181ae3e194
status: llm_drafted
---

# AdminFilesPage

## Purpose

The administrative interface for managing organization media files. It provides a centralized dashboard for viewing, uploading, filtering, and deleting files, specifically allowing administrators to toggle the `scope` (e.g., from "private" to "public") of uploaded assets. This is the primary UI for managing the organization's media library.

## Invariants

- **Upload scope is hardcoded to "private"** — The `handleUpload` function explicitly sets `{ scope: "private" }` for all new uploads.
- **Filtering is client-side** — The `filtered` constant performs search and scope/type filtering on the local `files` state rather than via API parameters.
- **File size display uses MB** — The `formatBytes` helper (implied by usage) converts raw bytes into a human-readable string with one decimal place.
- **Date rendering uses organization timezone** — The `formatDate` helper ensures all file timestamps are rendered in the org's local time via `formatInOrgTz`.

## Gotchas

- **Timezone-aware rendering is mandatory** — Per commit `f444b4c`, all backend datetimes must be rendered using `formatInOrgTz` to avoid displaying the viewer's local time instead of the organization's time.
- **Upload loop behavior** — The `handleUpload` function iterates through `fileList` and awaits each `mediaApi.upload` call sequentially. This means multiple file uploads are processed one-by-one, not in parallel.
- **State synchronization** — The `handleScopeChange` and `handleDelete` functions manually update the local `files` state after the API call succeeds to ensure the UI reflects the change without a full page reload.

## Cross-cutting concerns

- **Auth**: Requires authenticated admin access to interact with `mediaApi`.
- **Side effects**: Changes to file scope or deletions via this page will immediately affect any component consuming the `mediaApi` file list (e.g., public-facing asset galleries).

## External consumers

None known.
