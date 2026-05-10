---
node_id: concorda-web::src/components/boat/boat-events.tsx::BoatEvents
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d26fce4dc45cc88c8e7b1fe57ee2bdf72928ff3ae03ac53146dee1b32fc078a
status: current
---

# BoatEvents

## Purpose

Renders a list of upcoming or historical events (regattas) associated with a specific boat. It displays event names, status badges, date/time information, and any required positions or notes. This is a purely presentational component used within boat detail views to show the schedule.

## Invariants

- **Requires `boatId` and `events` array.** While `boatId` is passed in the props, the component primarily iterates over the `events` array to build the list.
- **Uses `formatInOrgTz` for all date rendering.** All timestamps must be passed through this helper to ensure the `timezone` from `useConstants()` is applied, preventing local browser time drift.
- **Status colors are driven by `STATUS_COLORS`.** The `variant` of the `Badge` is determined by the `event.status` string (e.g., "interested", "confirmed", "withdrawn").
- **Fallback naming.** If `event_name` is missing, it falls back to `regatta_name`, and finally to the string `"Unknown Event"`.

## Gotchas

- **Timezone rendering fix.** Per commit `f444b4c`, all backend datetimes must be rendered using the organization's timezone via `formatInOrgTz` rather than relying on the user's local browser time to avoid displaying incorrect event starts.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
