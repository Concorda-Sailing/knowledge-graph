---
node_id: concorda-web::src/app/members/admin/events/import-social/page.tsx::ImportContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 72ddce95f12f7b266e4578ed321c9460f116574a0e923d42e1915f2b35a58c76
status: llm_drafted
---

# ImportContent

## Purpose

The `ImportContent` component manages the two-stage workflow for importing event data from social media-related documents (like spreadsheets or single documents). It handles the file upload via `norApi.uploadAndExtract`, manages the transition from an "upload" phase to a "review" phase, and performs a duplicate check against existing events. It is distinct from a standard file upload in that it must parse the resulting data into a structured `ImportedItem` format for user verification before final submission.

## Invariants

- **Two-phase state machine**: The component transitions from `upload` to `review` only after the extraction and duplicate check are complete.
- **`norApi.uploadAndExtract` requirement**: The extraction logic relies on the `"social"` string identifier to route the file to the correct backend parser.
- **ID Generation**: Uses a combination of `Date.now()` and `Math.random().toString(36)` to create unique temporary IDs for items in the local `items` state.
- **Duplicate Detection**: The `adminEventsApi.checkDuplicates` call is triggered automatically after processing files to flag potential collisions with existing event names.

## Gotchas

- **Sequential Processing**: Files are processed one-by-one via a `Promise.resolve()` chain in `handleFiles` to avoid overwhelming the extraction service.
- **Data Normalization**: The `evtToForm` helper (referenced in `processFile`) is critical; if the shape of the extracted JSON from the backend changes, the `form` object may contain empty strings or unexpected types.
- **Mobile Layout**: Per commit `019f6e3`, the admin grids used to display these imported items require specific single-column reflow logic to remain usable on mobile devices.

## Cross-cutting concerns

- **Auth**: Requires authenticated admin session to access `norApi.uploadAndExtract` and `adminEventsApi.checkDuplicates`.
- **Side effects**: Successful imports eventually populate the event registry, affecting the "socials calendar" and "schedule detail view" mentioned in commit `fbb3579`.

## External consumers

None known.
