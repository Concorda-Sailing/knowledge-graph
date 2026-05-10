---
node_id: concorda-web::src/components/ui/calendar.tsx::Calendar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e3bc07c1480f65744a46a2bb56401fac9722159f6af15e9704e5efb80040c7be
status: llm_drafted
---

# Calendar

## Purpose

A styled wrapper around `react-day-picker` used to provide a consistent date-selection interface across the web application. It abstracts the complex `classNames` and `components` configuration required to match the Concorda design system, specifically handling the styling of navigation icons and day-range selection states. Use this instead of raw `DayPicker` to ensure consistent visual feedback for selected ranges and outside-month days.

## Invariants

- **Uses `DayPicker` as the base engine.** All props passed to `Calendar` are passed through to the underlying `DayPicker` component.
- **`showOutsideDays` defaults to `true`.** This ensures a continuous visual grid even when the current month view spans into adjacent months.
- **Navigational icons are hardcoded to `lucide-react`.** The `IconLeft` and `IconRight` components are pre-configured with `ChevronLeft` and `ChevronRight`.
- **Styling is driven by `classNames`.** The component uses a complex object to map `DayPicker` internal slots (like `cell`, `day_selected`, and `nav_button`) to Tailwind CSS classes.

## Gotchas

- **Complex CSS selectors for range selection.** The `cell` class uses a complex `[&:has(...)]` selector to handle the rounding of the start and end of a date range. If you modify the DOM structure or the selection logic, this specific styling for `day-range-end` and `day-range-middle` may break.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
