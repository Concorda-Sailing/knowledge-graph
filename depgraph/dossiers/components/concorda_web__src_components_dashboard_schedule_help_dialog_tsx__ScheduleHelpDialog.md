---
node_id: concorda-web::src/components/dashboard/schedule-help-dialog.tsx::ScheduleHelpDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9b63e41055fbb33db3ee70b4317d8913a5adff3d53f07b8d8f8615c4c6d1ab0f
status: current
---

# ScheduleHelpDialog

## Purpose

A purely informational UI component that provides a visual legend for the schedule card elements. It displays an annotated example of a schedule card (including date, race name, and location) to help users interpret the visual shorthand used in the dashboard. This is a static documentation tool and does not interact with any live data or state.

## Invariants

- **Static content.** The component renders a hardcoded example of a schedule card; it does not accept props or dynamic data.
- **Dialog-based interaction.** Uses the standard `Dialog` pattern with a `DialogTrigger` (a ghost-variant button) to manage visibility.
- **Visual consistency.** The example uses `tabular-nums` and specific color classes (e.g., `text-amber-600`) to match the actual schedule card's visual language.

## Gotchas

- **Manual visual sync.** Because the "example" is hardcoded HTML/JSX rather than a reusable sub-component, any changes to the actual `ScheduleCard` visual design (like icon sizes or badge styles) must be manually updated here to prevent the help dialog from becoming outdated.
- **Accessibility/UX.** The `DialogClose` button uses an `opacity-70` class which might be too subtle for high-contrast accessibility requirements, though it is standard for the current design system.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
