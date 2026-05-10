---
node_id: concorda-web::src/app/members/admin/events/races/[id]/page.tsx::RaceEditorContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d0dcd81f469b391088a5e95da8d9c19cdedb48fcdd480b2cf0b372e36402baf1
status: current
---

# RaceEditorContent

## Purpose

The primary editor component for race-specific details within a regatta. It manages the lifecycle of a race (creation vs. edit) by fetching data via `regattaApi.get(id)` and handling the transformation of local timezone-aware inputs into UTC ISO strings for the API. It is distinct from the `RegattaDetailSections` view-only component by providing a mutable form state and handling the `regattaApi` save/load logic.

## Invariants

- **Requires `events.view` permission** via the `PermissionGate` wrapper.
- **Uses `orgInputToUtcIso` for time conversion.** All `start` and `end` time strings must be converted from the organization's timezone to UTC before being sent to the server.
- **`isNew` flag logic.** If the `id` parameter is `"new"`, the component initializes with empty form fields and skips the initial `load()` call.
- **Form payload structure.** The `save` payload must explicitly map the `form` state to the API contract, specifically converting the `links` object (registration, nor, si, website) and the `start`/`end` times.

## Gotchas

- **Timezone conversion is mandatory.** Per commit `f1fcabf`, the component relies on `utcIsoToOrgInput` and `orgInputToUtcIso` to ensure the form displays and submits time correctly relative to the organization's timezone.
- **Location formatting.** Per commit `8cbe76e`, the UI logic must handle cases where only a location is set without causing layout breaks (e.g., dropping leading bullets).
- **View mode vs. Edit mode.** Per commit `74c5af6`, this component is the editor, but it relies on `RegattaDetailSections` for the display-only version of the data.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `PermissionGate`.
- **Side effects**: Updates the race data which is consumed by the sailing calendar and regatta detail views.

## External consumers

None known.
