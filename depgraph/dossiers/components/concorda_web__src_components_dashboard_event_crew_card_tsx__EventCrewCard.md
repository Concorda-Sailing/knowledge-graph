---
node_id: concorda-web::src/components/dashboard/event-crew-card.tsx::EventCrewCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 05d526bc129f7740aea5b05841d155e8fa30bb80118923c52e0f7646784c78e3
status: llm_drafted
---

# EventCrewCard

## Purpose

Displays and manages the crew composition for a specific event, distinguishing between those already assigned to the event and the available "pool" of people on the boat. It provides administrative actions like sending invites and resending notifications. Use this instead of `CrewPositionsCard` when you need to manage the actual membership (inviting/notifying) rather than just viewing roles.

## Invariants

- **`eventId` and `boatId` are required** to fetch both the event-specific crew and the boat-wide crew/pools.
- **`eventCrew` is the source of truth for status** (Invited, Accepted, Declined, or Pool).
- **Sorting is deterministic**: items are sorted by priority (ascending), then by first name, then by last name.
- **`onCrewChanged` must be called** after any mutation (like `sendCrewInvites`) to trigger a parent refetch and ensure the UI stays in sync with the server.

## Gotchas

- **`useWsFreshness` dependency**: The component listens to the `boat_crew.updated` event to trigger a reload. If an action (like `sendCrewInvites`) only updates the event-side state but not the boat-side state, the UI might feel stale until the next websocket pulse.
- **Toast dependency removal**: Per commit `3f37efe`, the `toast` call was removed from the `reload` function's dependencies to prevent infinite loops/unexpected UI behavior during re-renders.
- **Status-based filtering**: The "Available" list is a derived set calculated by checking if a `boatCrew` member is absent from the `eventCrew` or has a `POOL` status.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to call `eventsApi.sendCrewInvites` and `eventsApi.notifyCrew`.
- **Websocket**: Listens to `boat_crew.updated` via `useWsFreshness` to trigger a local `reload()`.
- **Side effects**: Triggers `onCrewChanged` which typically causes the parent dashboard or schedule view to refetch data.

## External consumers

None known.

## Open questions

- Should the "Available" pool logic be moved to a custom hook or a specialized utility if more complex filtering (like boat-specific constraints) is added?
