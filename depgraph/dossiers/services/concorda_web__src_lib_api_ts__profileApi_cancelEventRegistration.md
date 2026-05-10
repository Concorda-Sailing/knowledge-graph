---
node_id: concorda-web::src/lib/api.ts::profileApi.cancelEventRegistration
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9986502d26c4d7cd5874001166e8303c5f924aa926c3fa67dc7b504cc59ed3fa
status: llm_drafted
---

# profileApi.cancelEventRegistration

## Purpose
`cancelEventRegistration` is a service method used to remove a user's association with a specific event. It is a thin wrapper around a `DELETE` request to the `/api/profile/event-registrations/{id}` endpoint. A future agent should reach for this when a user needs to opt-out of an event they previously joined, such as via the `MyEventsList` component or the `UpcomingEvents` dashboard.

## Invariants
* HTTP Method: `DELETE`.
* Path: `/api/profile/event-registrations/${id}`.
* Auth: Requires an authenticated session via `fetchApiAuthenticated`.
* Return Shape: A JSON object containing a `{ message: string }`.
* Dependency: Relies on a valid registration `id` string.

## Gotchas
* **ID-based deletion**: The function expects a specific registration ID, not an event ID. Passing an event ID instead of the registration ID will result in a 404 or incorrect deletion.
* **UI State Sync**: Since this is a `DELETE` operation, the calling component (e.g., `MyEventsList`) must handle the local state update or re-fetch to ensure the removed registration disappears from the UI immediately.

## Cross-cutting concerns
* **Auth**: Requires a valid user session; failure to authenticate will result in a failed request.
* **Side Effects**: Successful cancellation likely impacts the "accepted count" and "slots" availability for the event, though this is handled server-side.

## External consumers
* `concorda-web::src/components/dashboard/upcoming-events.tsx` (via `UpcomingEvents`)
* `concorda-web::src/components/profile/my-events-list.tsx` (via `MyEventsList`)

## Open questions
* None.
