---
node_id: concorda-web::src/components/boat/boat-documents.tsx::BoatDocuments
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9f7079a1ac29200f6bf6b28331299fcc30758a5ceabb1be31bf2146cb1c558d7
status: llm_drafted
---

# BoatDocuments

## Purpose

Manages the lifecycle of non-photo media files (documents) associated with a specific boat. It provides an interface for uploading, deleting, and updating the visibility scope of files, specifically filtering out items with `document_type === "photo"` to avoid collision with the `boat-photos` component.

## Invariants

- **`entity_type` is fixed to `"boat"`** — All `mediaApi` calls for this component must use this string to ensure files are correctly associated with the boat entity.
- **`document_type` filtering** — The component explicitly filters out files where `document_type === "photo"` to prevent the document list from displaying media intended for the photo gallery.
- **`uploadScope` defaults to `"private"`** — New uploads are scoped to private by default unless the user explicitly changes the state via `handleScopeChange`.
- **`boatId` is the primary key** — The `fetchDocuments` effect and all mutation calls depend on a valid `boatId` string.

## Gotchas

- **Mobile layout regression** — Per commit `5c4b4a3`, the document filter stack and per-row category visibility can cause layout issues on mobile devices; ensure any UI changes to the list maintain the expected stacking behavior.
- **Photo collision** — If the `document_type` filter in `fetchDocuments` is removed or altered, the component will display photos, which breaks the separation of concerns between this component and the `boat-photos` component.

## Cross-cutting concerns

- **Auth**: Uses `mediaApi` which requires an authenticated session (bearer token).
- **Side effects**: Re-fetches the document list after every successful `upload`, `delete`, or `updateFile` to ensure the UI stays in sync with the server-side state.

## External consumers

None known.
