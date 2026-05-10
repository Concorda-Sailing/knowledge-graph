---
node_id: concorda-web::src/components/boat/boat-resume-view.tsx::BoatResumeView
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6781e30219da2a2fdbd8df00dc005f258dcc9828e6573c18780fb293166ffaa2
status: current
---

# BoatResumeView

## Purpose

The `BoatResumeView` component renders a read-only summary of a boat's operational profile. It transforms raw `resume` data into a structured, human-readable layout using the `Field` and `Chips` components. Use this when you need to display high-level availability, crew requirements, or race area preferences without the editable inputs found in the profile configuration views.

## Invariants

- **Input is a `BoatResumeViewProps` object** containing a `resume` object.
- **`availabilityValues` is derived from the `resume` object** via specific boolean flags (`weekends`, `evening_races`) rather than raw strings.
- **`whitespace-pre-line` is required for the "About" section** to preserve formatting of long-form text.
- **Uses `Empty` component for null/undefined values** to ensure the UI remains consistent and doesn't render empty-looking labels.

## Gotchas

- **Availability logic is hardcoded.** The component does not pass through all availability flags; it specifically maps `weekends` to "Weekends" and `evening_races` to "Weekday/Evening". If new availability types are added to the backend, they must be manually added to the `availabilityValues` array in this component to be visible.

## Cross-cutting concerns

- **Auth**: None (this is a pure presentational component).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
