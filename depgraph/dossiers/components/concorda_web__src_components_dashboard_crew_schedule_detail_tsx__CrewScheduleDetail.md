---
node_id: concorda-web::src/components/dashboard/crew-schedule-detail.tsx::CrewScheduleDetail
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e4b30773e7e80f19a7eb387f492e43059494a049ae41b368c08e6210050157f3
status: current
---

# CrewScheduleDetail

## Purpose

Displays the granular details of a specific schedule item, including its relationship to a regatta if applicable. It serves as the detail view when a user selects a specific event/item from the dashboard, providing context like location, time (formatted to the organization's timezone), and regatta-specific metadata (first warning, start area).

## Invariants

- **`item` is required.** The component expects a `ScheduleItem` containing an `event` object.
- **`regatta` is optional.** If `regatta` is null, the component only renders standard event details (name, date, location).
- **`isRace` logic.** A race is identified if `event.regatta_id` exists or `event.category === "regatta"`.
- **`onRemove` and `removing` props.** The component handles the UI state for a deletion flow, using the `removing` boolean to manage the "Remove" button interaction.

## Gotchas

- **Timezone rendering.** Per commit `f444b4c`, all backend datetimes must be rendered using `formatInOrgTz` with the `timezone` from `useConstants()`. Do not use native browser date formatting, as it will display the wrong time for the organization's local audience.
- **Print-specific styling.** The "Back" button and "Remove" button include the `print:hidden` class. Ensure any new action buttons intended for physical print-outs (like a printed schedule) are not accidentally hidden by this pattern.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: The `onRemove` callback triggers the deletion of a schedule item, which may affect the visibility of items in `ScheduleTab`.

## External consumers

None known.
