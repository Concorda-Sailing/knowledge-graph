---
node_id: concorda-web::src/lib/api.ts::seriesApi.generateRaces
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 296e119605c2f50b647728f3630a8007e39a9c8d0acc628d497171f4e26f290e
status: llm_drafted
---

# seriesApi.generateRaces

## Purpose

Triggers the server-side generation of races for a specific series. This is a destructive/transformative action that creates race instances based on the series configuration. It is distinct from `listRaces`, which merely fetches existing data; `generateRaces` is the command used to initiate the creation process.

## Invariants

- **HTTP Method is `POST`** — This is a command-style endpoint, not a pure retrieval.
- **Requires a valid `id`** — The series ID must be present in the URL path.
- **Returns a summary object** — The response shape is strictly `{ created: number; skipped: number; total: number }`.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute.

## Gotchas

- **Destructive/Additive behavior** — Because this generates new race instances, calling it multiple times may result in duplicate or unexpected race counts if the backend logic does not handle idempotency.
- **Dependency on Series Configuration** — The success of this call depends on the underlying series settings (e.g., number of races, spacing) being correctly configured before invocation.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Triggers the creation of new race records which will subsequently appear in `listRaces` and update the `SeriesDetailContent` view.

## External consumers

- `concorda-web::src/app/members/admin/events/import/page.tsx` (ImportRacesContent)
- `concorda-web::src/app/members/admin/events/series/[id]/page.tsx` (SeriesDetailContent)
