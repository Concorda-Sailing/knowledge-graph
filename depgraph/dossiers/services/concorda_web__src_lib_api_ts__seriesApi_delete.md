---
node_id: concorda-web::src/lib/api.ts::seriesApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9bd57e94a974c9b3234c3a19980a675d0e5416fcb86e208f571956736d3b1337
status: llm_drafted
---

# seriesApi.delete

## Purpose
`seriesApi.delete` provides a client-side interface to remove a specific series resource from the server. It is a destructive operation that should only be used when a user intends to permanently remove a series and its associated metadata. This function is distinct from `regattaApi.delete`, which targets different resource types. A future agent should reach for this function when implementing administrative "Delete" buttons or cleanup workflows within the Series management views.

## Invariants
* HTTP method is `DELETE`.
* Path follows the pattern `/api/series/{id}`.
* Requires authentication via `fetchApiAuthenticated`.
* Returns a `void` type on successful deletion.
* The `id` parameter must be a valid string representing the series identifier.

## Gotchas
* **Destructive Action**: This is a permanent deletion; ensure the UI provides a confirmation step before calling this function to prevent accidental data loss.
* **Dependency Integrity**: While this function deletes the series, the dossier does not explicitly state if deleting a series also cascades to delete associated regattas or race data on the server side.

## Cross-cutting concerns
* **Auth**: Requires a valid authenticated session via `fetchApiAuthenticated`.
* **Side Effects**: Deleting a series likely impacts any views or dashboards that rely on the existence of this series ID (e.g., the Series detail pages in `src/app/members/admin/events/series/[id]/page.tsx`).

## External consumers
* `concorda-web::src/app/members/admin/events/series/[id]/page.tsx` (SeriesDetailContent)
* `concorda-web::src/app/members/admin/events/series/page.tsx` (SeriesPage)

## Open questions
* Does the server-side implementation of the DELETE endpoint perform a hard delete or a soft delete (flagging the series as inactive)?
* Are there any downstream race conditions if a user attempts to `list` or `get` a series immediately after a `delete` call is initiated?
