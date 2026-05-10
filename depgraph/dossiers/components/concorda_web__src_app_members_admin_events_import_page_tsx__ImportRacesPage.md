---
node_id: concorda-web::src/app/members/admin/events/import/page.tsx::ImportRacesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 05a022324f53119d169e6b1a586abc9b8579817389855a9d0c5ad79320c0642b
status: current
---

# ImportRacesPage

## Purpose

Provides the administrative interface for importing race data via Notice of Race (NOR) files. It manages a two-phase workflow: an initial upload/extraction phase using `norApi.uploadAndExtract` and a subsequent review phase where extracted data is displayed and can be corrected before final submission.

## Invariants

- **Requires `events.view` permission** via the `PermissionGate` wrapper.
- **Uses `norApi.uploadAndExtract(file, "nor")`** to perform the heavy lifting of parsing the uploaded file.
- **Extraction mapping is complex and hierarchical**: The function extracts fields like `name`, `start`, `location`, and `description` from a nested structure that may prioritize `regatta` or `event` keys depending on the API response shape.
- **State-driven phases**: The UI transitions between `"upload"` and `"review"` based on the `phase` state.

## Gotchas

- **Timezone-aware rendering is mandatory**: Per commit `f444b4c`, all backend datetimes extracted during this process must be rendered in the organization's timezone, not the browser's local time, to avoid scheduling errors.
- **Complex field mapping**: The extraction logic (lines 61-84) relies on a specific fallback chain (e.g., `reg?.name || evt?.name || ""`). If the `norApi` response structure changes, the `form` object construction will break or produce empty strings.
- **Sequential processing**: The `processFile` function uses a `queue` and `setQueue` pattern to handle files one by one, ensuring the UI doesn't become overwhelmed by concurrent uploads.

## Cross-cutting concerns

- **Auth**: Wrapped in `PermissionGate` with `events.view`.
- **Side effects**: Successful imports/extractions are intended to eventually populate the event registry, though the final submission logic is handled by the child components/subsequent steps.

## External consumers

None known.
