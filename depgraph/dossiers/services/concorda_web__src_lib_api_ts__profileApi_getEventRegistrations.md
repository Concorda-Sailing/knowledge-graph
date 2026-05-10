---
node_id: concorda-web::src/lib/api.ts::profileApi.getEventRegistrations
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 011459cae90ece78cde36273cd0be769c444e027d9a5803b813d5dbae8fcfc11
status: current
---

# profileApi.getEventRegistrations

## Purpose

Fetches the list of events a specific user is currently registered for. It is used to populate user-facing lists that show upcoming commitments, such as the "My Events" view and the dashboard. Use this instead of `eventsApi` when you need to filter the global event list down to the authenticated user's specific participation.

## Invariants

- **GET request** to `/api/profile/event-registrations`.
- **Requires authentication** via `fetchApiAuthenticated`.
- **Returns an array of `MyEventRegistration` objects**, which are specialized versions of the `Event` interface.
- **Data is user-centric**; the response is scoped to the identity of the bearer token.

## Gotchas

- **Coupling with schedule detail:** Per commit `1b5d864`, this endpoint is distinct from the `/api/events/{id}/detail` pattern. Avoid attempting to merge registration state into the general event detail endpoint to prevent tight coupling between the global schedule and user-specific profiles.
- **Count vs. Live State:** Per commit `b4d60c6`, ensure that UI components using this data distinguish between "accepted invites" and "live slot counts." This endpoint provides the registration record, but the actual availability of slots is driven by the event's configuration.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is scoped to the logged-in user.
- **Side effects**: Updates to the registration state (via `cancelEventRegistration`) will affect the visibility of items in the `UpcomingEvents` component and the `MyEventsList` component.

## External consumers

- None known.
