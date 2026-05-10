---
node_id: concorda-web::src/components/dashboard/regatta-help-dialog.tsx::RegattaHelpDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d683812015997f6bc80bff143e038b03d8c65fc1117fc6c7b12337e86443d6da
status: llm_drafted
---

# RegattaHelpDialog

## Purpose

Provides an instructional overlay for the Race Calendar (Regatta) view. It displays a visual guide explaining the meaning of various UI elements—such as status badges, location details, and venue information—using an annotated example. This ensures users can interpret the complex data-driven rows in the schedule correctly.

## Invariants

- **Uses a `Dialog` pattern** to prevent blocking the main dashboard view.
- **The trigger is a `Button` with `variant="ghost"`** and a specific `aria-label="Race calendar help"` to maintain visual consistency with the dashboard's utility icons.
- **The content is scrollable** via `max-h-[90vh] overflow-y-auto` to ensure the full guide is accessible on smaller screens or laptop displays.
- **The header is `sticky top-0`** to keep the title and close button visible while the user scrolls through the annotated examples.

## Gotchas

- **Close button styling/accessibility:** Per commit `4bdf12b`, the `X` close button was explicitly updated to include a `sr-only` span for screen readers and specific `opacity-70` hover states to ensure it doesn't interfere with the visual hierarchy of the header.
- **Documentation of data fields:** Recent documentation updates (commit `3756375`) suggest the guide must explicitly cover the "OA · city/state · region" row format to prevent user confusion regarding location data.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: The dialog is a purely presentational helper for the dashboard; it does not trigger state changes in the `EventsCalendar` or `ScheduleTab`.

## External consumers

None known.
