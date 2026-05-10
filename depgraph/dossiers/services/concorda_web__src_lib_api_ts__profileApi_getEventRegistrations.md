---
node_id: concorda-web::src/lib/api.ts::profileApi.getEventRegistrations
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 011459cae90ece78cde36273cd0be769c444e027d9a5803b813d5dbae8fcfc11
status: llm_drafted
---

# profileApi.getEventRegistrations

## Purpose
Fetches the list of all events a specific user is currently registered for. This is a read-only retrieval of the user's personal event participation history. Use this when building views that require a list of a user's upcoming commitments, such as the "My Events" section or dashboard summaries. It is distinct from `eventsApi` calls which fetch general event details; this is strictly scoped to the authenticated user's profile.

## Invariants
* HTTP Method: GET.
* Path: `/api/profile/event-registrations`.
* Auth: Requires an authenticated session via `fetchApiAuthenticated`.
* Return Shape: An array of `MyEventRegistration` objects.
* Dependency: Relies on the server-side session to identify the user.

## Gotchas
* The return type is `MyEventRegistration[]`, which is a specialized view of an `Event` tailored for the user's profile context.
* Ensure the UI handles empty arrays gracefully if a user has no active registrations.

## Cross-cutting concerns
* Auth: Requires a valid user session; calls will fail with 401/403 if the user is unauthenticated.
* Side Effects: This is a pure GET request and does not trigger state changes in the event system.

## External consumers
* `concorda-web::src/components/dashboard/upcoming-events.tsx` (UpcomingEvents component)
* `concorda-web::src/components/profile/my-events-list.tsx` (MyEventsList component)

## Open questions
* None.
