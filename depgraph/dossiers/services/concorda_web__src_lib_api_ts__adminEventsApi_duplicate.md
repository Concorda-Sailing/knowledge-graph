---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.duplicate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0abc97b73ac355a348bca469d9395cc937570c66dfb34c55c164bed15648df96
status: current
---

# adminEventsApi.duplicate

## Purpose

Creates a copy of an existing event via a POST request to the `/api/events/{id}/duplicate` endpoint. This is used by administrators to quickly replicate event configurations. It is distinct from `uploadImage` or `deleteImage` as it handles the high-level duplication of the event entity itself rather than its assets.

## Invariants

- **Method is `POST`** — The operation is a creation-via-copy, requiring a POST request.
- **Requires an existing `id`** — The function takes a string `id` representing the source event to be duplicated.
- **Returns an `Event` object** — The successful response shape is the full `Event` entity of the newly created duplicate.
- **Uses `fetchApiAuthenticated`** — The request must include a valid bearer token to satisfy the administrative authorization requirement.

## Gotchas

- **Recent coupling issues** — Per commit `1b5d864`, the system is moving away from tight coupling between event details and specific schedule views; ensure that duplicating an event does not inadvertently carry over stale or incorrect schedule-specific state if the API implementation is not idempotent regarding sub-resources.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `fetchApiAuthenticated`.
- **Side effects**: Duplicating an event may trigger downstream updates in the event list and potentially impact the `EventDetailContent` view in `src/app/members/admin/events/[id]/page.tsx`.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailContent`
