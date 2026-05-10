---
node_id: concorda-test::lib/api-client.ts::ApiClient.listEvents
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 29c2d0a817b5213086cb7afd35ebbe687dd993dce8fe7a92418b01ce342fcc57
status: current
---

# ApiClient.listEvents

## Purpose

Fetches the full list of events from the `/api/events` endpoint. This is the primary method for retrieving the global event registry, used by tests to verify event existence, registration flows, and schedule-related visibility. It is distinct from `listMySchedule`, which is a filtered view of personal/bookmarked events, and `getEventBySlug`, which targets a specific event.

## Invariants

- **HTTP Method is `GET`** — calls the `/api/events` endpoint.
- **Returns an Array of Objects** — the response is a `Promise<Array<Record<string, unknown>>>`.
- **Requires Authentication** — as a standard `ApiClient` method, it relies on the bearer token established via `login`.

## Gotchas

- **Remote Host Alignment** — per commit `917acfe`, the API client is frequently pointed at a remote test host rather than localhost. Ensure any changes to the endpoint structure or connectivity are compatible with the remote test environment.
- **Integration with UI State** — per commit `c8b6d75`, this method is central to the "My Schedule" view logic. Changes to the shape of the returned event objects can break the integration between the API client and the UI components that display the schedule.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token (established via `ApiClient.login`).
- **Side effects**: Used to verify visibility in the "My Schedule" view and the "Boats" tab (per commit `c8b6d75`).

## External consumers

None known.
