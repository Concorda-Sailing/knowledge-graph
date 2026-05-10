---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fea68e71bea6977d73cd259096137c3556db2ff03e494443c839f6abc9e9ce0
status: llm_drafted
---

# adminEventsApi.create

## Purpose

Provides the administrative interface for creating new event records. This method is the primary entry point for adding events to the system via the web dashboard. It is distinct from `eventsApi.addRegattas` (which is a specialized bulk operation) and is used when a full `EventCreate` payload is required for a new event instance.

## Invariants

- **HTTP Method is `POST`** — Always targets `/api/events`.
- **Requires `fetchApiAuthenticated`** — The call must include a valid bearer token; it will fail if the user is not authenticated.
- **Returns `Promise<Event>`** — The response body is the newly created event object.
- **Payload is `EventCreate`** — The input must match the `EventCreate` interface to ensure all required fields (like `name` and `date`) are present.

## Gotchas

- **Implicit dependency on `boat_config_id`** — Per commit `bf15808`, the API expects a specific shape for boat-related data; ensure the `EventCreate` payload uses the correct ID field rather than a raw object to avoid shape-matching errors.
- **Relationship to `requestToCrew`** — Commit `f876f14` indicates that event creation/updates are sensitive to how `boat_uuid` is passed through the request to maintain correct crew associations.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Creating an event via this method triggers updates to the `EventDetailContent` page and is a prerequisite for the `ImportContent` flow in the social import module.

## External consumers

None known.
