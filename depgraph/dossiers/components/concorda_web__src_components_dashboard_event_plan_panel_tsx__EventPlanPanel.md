---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::EventPlanPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d4b24b27967a56d6845c3df6a60fdc14febed2864e96c99eb85fbc0c7477fc4
status: current
---

# EventPlanPanel

## Purpose

The `EventPlanPanel` is a specialized editing interface for a `ScheduleItem`. It allows users to modify event-specific details such as the assigned boat, departure/arrival locations, and crew configurations. It is distinct from a general "edit event" form because it is deeply coupled to the `ScheduleItem` structure, specifically managing the relationship between a sailing event and its associated boat, crew pools, and time-based constraints.

## Invariants

- **Input is a `ScheduleItem`** — The component expects an object containing both an `event` (for date/time) and a `sailing_event` (for boat/crew/location details).
- **Time handling is two-way** — It uses `formatInOrgTz` for display and `orgInputToUtcIso` for storage to ensure the wall-clock time remains anchored to the organization's timezone.
- **Boat change resets state** — Changing the `boat_uuid` via `handleBoatChange` must reset `config_id`, `slots`, and `eventCrew` to prevent stale data from a previous boat being saved to a new one.
- **Defaulting logic** — If no boat is explicitly assigned to the `sailing_event`, it attempts to default to the first available boat in the `boats` context or the `homePort` of the current boat.

## Gotchas

- **Timezone anchoring** — Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. If you use a standard `Date` object or a different formatter, the dock/departure times will drift from the intended wall-clock time seen by the editor.
- **API Scoping** — Per commit `2e089b2`, the `crew-pools` API and UI are scoped strictly to a boat. When implementing changes to crew selection, ensure the `boatId` is passed to the correct profile/boat API endpoints to avoid unauthorized or empty results.
- **Form/State Sync** — The `departure_location` and `arrival_location` are conditionally updated during `handleBoatChange` to ensure they don't become invalid if the previous boat's port is no longer applicable.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` and `boatApi` which require authenticated sessions.
- **Websocket**: none
- **Audit**: Y (Modifying these fields via the parent `ScheduleTab` or similar triggers updates to the event/schedule state).
- **Rate limit**: none
- **Side effects**: Updates to this panel directly affect the `ScheduleTab` view and the `EventsCalendar` display via the underlying `ScheduleItem` data.

## External consumers

None known.
