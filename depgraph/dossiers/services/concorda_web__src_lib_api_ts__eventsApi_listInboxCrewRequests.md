---
node_id: concorda-web::src/lib/api.ts::eventsApi.listInboxCrewRequests
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e825507568483a3080d59a3baa6e16b86fd081fa7b817cafcd3617c9fac6cd03
status: current
---

# eventsApi.listInboxCrewRequests

## Purpose

Fetches the list of pending crew requests for boats owned by the authenticated viewer. This serves as the primary data source for the "Inbox" feature, allowing boat owners to see and manage incoming requests to join their vessels. It is a specialized view of the crew request lifecycle, distinct from the general event-level requests.

## Invariants

- **Uses `fetchApiAuthenticated`** — Requires a valid session/bearer token to access the `/api/events/crew-requests/inbox` endpoint.
- **Returns `CrewRequestInboxItem[]`** — The response is an array of objects containing the necessary context to display a request (e.g., person, boat, and event details).
- **GET request** — The underlying API call is a standard GET to the inbox endpoint.

## Gotchas

- **Ownership dependency** — Per the docstring, this only returns requests for boats the viewer actually owns. If a user is looking for requests for a boat they are merely a member of, this will return an empty list.
- **Recent logic shifts** — Commit `b4d60c6` addressed issues with how accepted invites are counted versus live slot counts; ensure that any UI consuming this list correctly handles the distinction between a "pending" request and a "confirmed" position.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires user session).
- **Side effects**: Powers the "Inbox" view and the count of incoming requests for boat owners.

## External consumers

- `use-inbox-crew-requests.ts` (via `fetchNow` hook).
