---
node_id: concorda-web::src/components/dashboard/schedule-card.tsx::ScheduleCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f29aa5fddd3fd369929d6705dc144398bb9bf867e96ffc0a219776867dc4b27e
status: current
---

# ScheduleCard

## Purpose

The `ScheduleCard` is a visual representation of a single event (race or social) within a user's dashboard. It provides a high-level summary of the event's date, name, type (Race/Social), and current crew status. It is distinct from the `CrewPositionsCard` in that it focuses on the event's temporal identity and high-level metadata, whereas the positions card handles the granular breakdown of specific crew slots.

## Invariants

- **Timezone-aware rendering**: The date block (day of week and day number) must be rendered using the organization's timezone (`tz`) via `Intl.DateTimeFormat` to ensure the "Today/Tomorrow" countdown remains semsantically aligned with the user's local context.
- **Slot count fallback**: The component must prioritize the live `BoatConfig` slot count (`se?.config_slot_count`) for accuracy, falling back to the `positions_needed` array length for legacy events lacking a `boat_config_id`.
- **Role-based visibility**: The component uses `viewer_role` to determine if the view is "Shared" (co-owner status) or "Crew" (active `EventCrew` row), which dictates the badges and help-dialog context displayed.

## Gotchas

- **Off-by-one date errors**: Per commit `cff2420`, the date rendering logic must be careful with events occurring near midnight; failing to use the organization's `tz` for the `dayOfWeek` and `dayNum` calculation can cause the "Today/Tomorrow" countdown to be visually inconsistent with the actual calendar day.
- **Legacy event compatibility**: If a `sailing_event` lacks a `boat_config_id`, the component relies on `positions.length` for the `totalSlots` calculation. Ensure any logic involving slot counts accounts for this fallback to avoid breaking legacy event displays.
- **Crew status visibility**: Per commit `6eace6a`, the component is designed to hide specific peer crew status from non-owner viewers to maintain privacy/security boundaries.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to retrieve the current `user.id` for calculating `myPosition`.
- **Side effects**: Updates to the `BoatConfig` or `EventCrew` status will change the `totalSlots` and `acceptedCount` displayed here; the component relies on the parent dashboard to trigger re-renders when these underlying data structures change.

## External consumers

None known.
