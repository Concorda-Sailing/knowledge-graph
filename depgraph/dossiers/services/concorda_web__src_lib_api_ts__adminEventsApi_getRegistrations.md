---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.getRegistrations
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 673262a138bd49b660c54b9977f2788df761ac83401355ceaa74e00a3c7db73a
status: llm_drafted
---

# adminEventsApi.getRegistrations

## Purpose

Fetches the list of all registrations associated with a specific event ID. It is used by administrative views to display participant data for a given event. Use this method when you need the full array of `EventRegistrationResponse` objects rather than just a count.

## Invariants

- **Requires an event `id`** as a string parameter.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to resolve.
- **Returns an array of `EventRegistrationResponse` objects.**
- **Endpoint path is `/api/events/${id}/registrations`**.

## Gotchas

- **Recent logic changes in `b4d60c6`** suggest that registration-related data (like counts and status) is frequently decoupled from the main event object to avoid stale state; ensure you are calling this fresh if you need the most recent registration list.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Data returned here is used by the `EventDetailContent` component in `src/app/members/admin/events/[id]/page.tsx`.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailContent`
