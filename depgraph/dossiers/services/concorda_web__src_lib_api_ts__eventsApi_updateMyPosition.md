---
node_id: concorda-web::src/lib/api.ts::eventsApi.updateMyPosition
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 672506fca43f8a6dfb68fc585ea00066293dae9a8a2e036b591272f5916c85e6
status: current
---

# eventsApi.updateMyPosition

## Purpose

Updates the current user's position/role within a specific sailing event. It is used to transition a user from a "pending" or "unassigned" state to a specific role (e.g., "Skipper", "Crew") or to clear their position by passing `null`. This is a distinct action from `respondToCrewRequest`, which is used for accepting or declining an explicit invitation.

## Invariants

- **Method is `PUT`** — updates the existing resource rather than creating a new one.
- **Requires `eventId` and `positionName`** — the `positionName` can be a string or `null` to clear the position.
- **Returns `EventCrewMember`** — the response shape is the updated membership object.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute.

## Gotchas

- **Avoid "position-name gating"** — per commit `b3adc60`, the system moved away from using the presence of a name to determine status; ensure the UI doesn't rely on a non-null string to imply a successful state change if the backend logic has evolved.
- **Relationship to `EventCrewStatus`** — per commit `bf44b09`, the backend now uses a specific `EventCrewStatus` type union; ensure the `positionName` passed matches the expected string literals for the specific event type to avoid silent failures or unexpected state.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires user session).
- **Side effects**: Updates the state of the `ScheduleEventDetail` page (specifically `concorda-web::src/app/members/schedule/[id]/page.tsx`).

## External consumers

None known.
