---
node_id: concorda-web::src/components/dashboard/event-crew-pool-selector.tsx::EventCrewPoolSelector
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85406e8245a51e76a4a3888dbf3f8e7e85372010fb285bc99ce375ecd325faae
status: current
---

# EventCrewPoolSelector

## Purpose

Manages the selection of a "crew pool" for a specific event, allowing admins to toggle between a specific group of people or an "All" view. It distinguishes between the permanent boat crew (who are always present) and the event-specific crew. Use this component when an admin needs to define which members of a boat's active crew are actually participating in a specific event.

## Invariants

- **`activeGroupId` state logic**: Uses a three-state pattern to distinguish between "no group selected" (`undefined`), "All members active" (`null`), and a specific named group (`string`).
- **`onPoolUpdated` callback**: Receives the result of `eventsApi.setCrewPool` to ensure the parent component stays in sync with the server-side state.
- **Selection logic**: The "All" option (`groupId === null`) must include both the `selectableUuid` set (active boat crew) and the `lockedUuids` (members with non-pool status).
- **Owner exclusion**: The `selectable` filter explicitly removes any user with the `role === "owner"` to prevent the owner from being "unselected" from their own boat.

## Gotchas

- **The "All" toggle behavior**: Per the implementation of `applyGroup`, selecting "All" (or a named group) and then clicking it again toggles the selection back to the `existingUuids` (the original event crew) rather than an empty set.
- **Sentinel values**: Developers must be careful with the `activeGroupId` type; `undefined` is a deliberate sentinel for "no group active," whereas `null` represents the "All" group.
- **API dependency**: Relies on `eventsApi.setCrewPool`. If the payload shape for `setCrewPool` changes (e.g., requiring more than just a list of UUIDs), this component will fail to update the event state.

## Cross-cutting concerns

- **Auth**: None (assumes parent component handles event-level permissions).
- **Websocket**: None.
- **Audit**: Y (triggers `eventsApi.setCrewPool` which logs the change to the event's crew composition).
- **Rate limit**: None.
- **Side effects**: Updates the event's crew list, which may affect the visibility of members in the `ScheduleTab` or `CrewPositionsCard`.

## External consumers

None known.
