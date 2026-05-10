---
node_id: concorda-web::src/app/members/admin/events/series/[id]/page.tsx::SeriesDetailContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b214587d20355e71de6e63994eeb098a9b2ad02b524ced2163130f4f8e770093
status: llm_drafted
---

# SeriesDetailContent

## Purpose

The administrative interface for managing a specific event series. It handles the fetching, display, and editing of series metadata, including name, description, scoring systems, and associated organizing authorities. It is distinct from the race-level management views by focusing on the high-level container (the series) and its temporal bounds.

## Invariants

- **Requires `events.view` permission** via the `PermissionGate` wrapper.
- **Uses `orgDateInputToUtcIso` for all datetime transformations** to ensure the `start` and `end` fields are stored as UTC ISO strings in the backend.
- **Converts `scoring_system` and `qualifier` from comma-separated strings to arrays** during the save process.
- **Parses `num_races` as an integer** before sending the update to the API.
- **Relies on `seriesId` from `useParams()`** to drive all data fetching and updates.

## Gotchas

- **Timezone-aware rendering is mandatory.** Per commit `f444b4c`, all backend datetimes must be rendered using the organization's timezone via `utcIsoToOrgDateInput` to prevent the UI from displaying browser-local times.
- **Form state synchronization:** The `populateForm` function is used to map the API response (UTC/ISO) into the local form state (Org-timezone-aware strings) to ensure the input fields match what the user expects to see based on the organization's local time.

## Cross-cutting concerns

- **Auth**: Protected by `PermissionGate` with `events.view`.
- **Side effects**: Updating a series via `seriesApi.update` affects the display of the series in the event calendar and any race-level detail pages that rely on the series' temporal bounds.

## External consumers

None known.
