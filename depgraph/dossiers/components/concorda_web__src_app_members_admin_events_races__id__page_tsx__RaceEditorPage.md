---
node_id: concorda-web::src/app/members/admin/events/races/[id]/page.tsx::RaceEditorPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7566351a28c78ab30a9187a537186cb565e500d27895cc35b086c6dcb4fb5ed4
status: llm_drafted
---

# RaceEditorPage

## Purpose

Provides the administrative interface for creating or editing a Race (Regatta). It handles the dual-mode lifecycle of fetching existing data via `regattaApi.get(id)` or initializing a blank state when `id === "new"`. It manages a complex local form state that synchronizes UTC ISO strings from the API into the organization's local timezone for user-friendly editing.

## Invariants

- **Permission Gate**: The entire page is wrapped in `<PermissionGate permission="events.view">`, ensuring only authorized admins can access the editor.
- **Timezone Synchronization**: Uses `utcIsoToOrgInput(..., timezone)` to convert API timestamps into editable local strings; failure to use this results in incorrect time offsets in the form.
- **Form Payload Structure**: The `handleSave` function must explicitly map the local `form` state (which includes human-readable strings) back to the API-compatible payload, specifically handling the `links` sub-object for URLs.
- **Mandatory Fields**: The `name` field is strictly required; the save process is aborted with a toast if `form.name.trim()` is empty.

## Gotchas

- **Leading Bullet Bug**: Per commit `8cbe76e`, the UI previously had issues with leading bullets when only location was set; ensure any logic modifying the `location` or `start_area` strings does not introduce unintended formatting artifacts.
- **View Mode vs. Edit Mode**: The component uses `RegattaDetailSections` for display-only modes, but this specific page is the editor. Be careful not to accidentally replace the editor logic with the read-only view component.
- **Data Type Coercion**: The `populateForm` function performs heavy coercion (e.g., `.toString()` for `max_races` and `.join(", ")` for arrays). If the API schema for `RegattaDetail` changes to strictly typed numbers or objects, this function will break.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `PermissionGate`.
- **Side effects**: Updates the regatta record, which propagates changes to the sailing calendar and any linked race detail views.

## External consumers

None known.
