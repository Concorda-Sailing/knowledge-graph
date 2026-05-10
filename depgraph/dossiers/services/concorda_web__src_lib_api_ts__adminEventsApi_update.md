---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0b0d1e89508085dc7e4b4ae768b7c811c246a93ab9e933649d3f9c3f9b4dfd81
status: current
---

# adminEventsApi.update

## Purpose

The `update` method performs a partial or full update of an existing event via a `PUT` request. It is the primary way to modify event metadata (like name, date, or configuration) through the admin interface. Use this when you need to persist changes to an existing event resource identified by `id`.

## Invariants

- **HTTP Method is `PUT`** — unlike `duplicate` which uses `POST` to create a copy, `update` modifies the existing resource.
- **Requires `fetchApiAuthenticated`** — the request must include a valid bearer token to pass the server-side authorization guard.
- **Returns the updated `Event` object** — the response body contains the full, updated event state.
- **Input is an `EventUpdate` type** — the payload must conform to the `EventUpdate` interface to ensure compatibility with the API's expected schema.

## Gotchas

- **Recent schema changes affect payload shape** — commit `bf15808` fixed a bug where the API was using shape-matching instead of a specific `boat_config_id`; ensure any data being sent to `update` respects the current `EventUpdate` structure rather than relying on implicit shape matching.
- **Dependency on `EventDetailContent`** — this method is directly used by the event detail page (`page.tsx:521`). Changes to the return shape of `update` will immediately break the detail view's ability to render the updated state.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has administrative permissions to modify event data.
- **Side effects**: Updates to event data via this method will affect the visibility of event details on the "regatta detail" view and any components relying on the `Event` object state.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (EventDetailContent)
