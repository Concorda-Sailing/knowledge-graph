---
node_id: concorda-web::src/lib/api.ts::eventsApi.registerAuthenticated
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d1bfb052f315f28d356ed89bf5a11bd316901beedf033ba9500b5cb9513bebe0
status: current
---

# eventsApi.registerAuthenticated

## Purpose

Provides authenticated endpoints for event registration and personal schedule management. It is the authenticated counterpart to the public `register` method; use this when the user is logged in and needs to link an event/regatta to their personal schedule or manage their own event details.

## Invariants

- **Method is POST/PUT/DELETE** — All methods in this set involve state changes (registration, updating, or removing schedule items).
- **Requires `fetchApiAuthenticated`** — Every method relies on a valid bearer token to identify the user performing the action.
- **Returns `EventRegistrationResponse` or `ScheduleItem[]`** — The return types are strictly typed to match the specific action (e.g., registration success vs. schedule list).
- **`departure_time` defaults to `dock_time + 45m`** — This client-side logic is expected for regatta/series additions.

## Gotchas

- **`mySchedule` coupling** — Per commit `1b5d864`, the detail page was previously coupled to `mySchedule`, but it now calls `/api/events/{id}/detail` directly to avoid unnecessary dependency on this specific schedule-view logic.
- **`boat_uuid` requirement** — Per commit `f876f14`, ensure `boat_uuid` is passed through `requestToCrew` to maintain correct context during crew-related requests.
- **Role-based access** — Per commit `47688ac`, certain operations (like accepting co-owner invites) now require `Boat Owner` membership, which may cause 403s if the user's role is insufficient.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session/token).
- **Side effects**: Updating or adding events via these methods triggers updates to the "my-schedule" view and can affect the "accepting-crew" status/badge on regatta detail pages.

## External consumers

None known.
