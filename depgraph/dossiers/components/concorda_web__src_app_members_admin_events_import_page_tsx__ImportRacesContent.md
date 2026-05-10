---
node_id: concorda-web::src/app/members/admin/events/import/page.tsx::ImportRacesContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: be6b3cbcd6825f010d06b76b4a2f73e3fe2e5e492efb8b2b4e70b7647e276cab
status: current
---

# ImportRacesContent

## Purpose

Manages the multi-step workflow for importing race data via Notice of Race (NOR) files. It handles the file upload, calls the `norApi.uploadAndExtract` service to parse the document, and provides a review interface where the extracted data (name, dates, location, etc.) can be verified or corrected before final submission. It is distinct from the `ImportSocialsPage` which handles social-specific event data.

## Invariants

- **Permission Gate**: The component is wrapped in a `PermissionGate` requiring `events.view`.
- **Extraction Logic**: The `processFile` function maps the raw `norApi` response into a flat `form` object with specific string-casting for fields like `start`, `end`, and `location`.
- **State Transition**: The UI moves through a `phase` of either `"upload"` or `"review"`.
- **Data Normalization**: Complex fields like `qualifier`, `classes`, and `scoring_system` are joined into comma-separated strings during the extraction mapping to ensure compatibility with the backend form schema.

## Gotchas

- **Timezone Sensitivity**: Per commit `f444b4c`, all backend datetimes extracted from the file must be rendered in the organization's timezone rather than the browser's local time to avoid offset errors in the review UI.
- **Complex Field Mapping**: The mapping logic for `qualifier` and `classes` (lines 64-65) relies on manual type checking and array joining; if the `norApi` returns a different structure for these fields, the `String()` casting or `.join()` calls may fail or produce unexpected strings.
- **Sequential Processing**: The `handleFiles` function (lines 102-107) uses a `reduce` chain to process files sequentially. This ensures the `queue` and `items` state updates don't collide during rapid multi-file uploads.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `PermissionGate`.
- **Side effects**: Successful imports via this component eventually populate the event registry, affecting the sailing calendar and event-specific views.

## External consumers

None known.
