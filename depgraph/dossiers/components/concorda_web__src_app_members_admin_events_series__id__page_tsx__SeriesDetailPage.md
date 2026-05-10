---
node_id: concorda-web::src/app/members/admin/events/series/[id]/page.tsx::SeriesDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a52774517c396609e9e4acff26864322639b3b40566fe50ade30f073ddcfa41d
status: llm_drafted
---

# SeriesDetailPage

## Purpose

The administrative detail view for a specific event series. It allows administrators to view and edit core series metadata, including name, description, start/end times, scoring systems, and associated organizing authorities. It serves as the primary interface for managing the high-level scheduling and structural properties of a series before individual races are managed.

## Invariants

- **Permission Guarded** — The entire view is wrapped in a `<PermissionGate permission="events.view">`.
- **Timezone-Aware Form Round-tripping** — Uses `utcIsoToOrgDateInput` to populate the form and `orgDateInputToUtcIso` to save it, ensuring the user edits in the organization's local time while the API receives UTC.
- **State Synchronization** — The `load` function performs a dual fetch of the series object and its constituent races via `seriesApi.get` and `seriesApi.listRaces`.
- **Data Transformation** — The `populateForm` function converts raw API strings (like `scoring_system` and `qualifier`) into comma-separated strings for the editable text inputs.

## Gotchas

- **Timezone Rendering** — Per commit `f444b4c`, all backend datetimes must be rendered using organization-specific timezone helpers. Using standard `Date` methods or local browser time for the `start` and `end` inputs will result in incorrect time offsets being sent back to the API.
- **Manual String Parsing** — The `handleSave` function performs manual `.split(",").map(...)` on `scoring_system` and `qualifier`. If these fields are left empty or malformed, the logic relies on the `filter(Boolean)` and `undefined` assignment to maintain a clean API payload.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `PermissionGate`.
- **Side effects**: Updates to this page (via `seriesApi.update`) affect the visibility and timing of all child races within this series.

## External consumers

None known.
