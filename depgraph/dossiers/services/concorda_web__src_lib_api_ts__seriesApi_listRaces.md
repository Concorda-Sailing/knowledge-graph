---
node_id: concorda-web::src/lib/api.ts::seriesApi.listRaces
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0aaf225e1290bba0d4b61722fd1094ceeb4ae0d484c15430801e77c4e5759b6b
status: llm_drafted
---

# seriesApi.listRaces

## Purpose

Fetches the list of races associated with a specific series. This is a read-only GET request used to populate race-level views within a series context. Use this when you need to display the constituent parts of a series (e.g., a list of regattas or events) rather than the series metadata itself.

## Invariants

- **HTTP Method**: `GET`
- **Endpoint Path**: `/api/series/${id}/races`
- **Auth**: Requires a valid bearer token via `fetchApiAuthenticated`.
- **Return Shape**: Returns an array of `RegattaDetail` objects.

## Gotchas

- **Dependency on Series ID**: The `id` passed must be the series identifier, not a regatta identifier.
- **Implicit dependency on `generateRaces`**: If the list appears empty or outdated, it may be because `seriesApi.generateRaces` has not been called to populate the series-to-race relationship.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to view the series content.
- **Side effects**: Changes to the underlying races (via `regattaApi.update` or `seriesApi.generateRaces`) will change the output of this call.

## External consumers

- `SeriesDetailContent` in `src/app/members/admin/events/series/[id]/page.tsx`.

## Open questions
