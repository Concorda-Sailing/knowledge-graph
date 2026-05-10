---
node_id: concorda-web::src/lib/api.ts::regattaApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d42747dd0c24d777e2b02cf6454d9b9c73fbc19f7a3b23280d4ebead31cd31f6
status: llm_drafted
---

# regattaApi.create

## Purpose

Creates a new regatta (SailingEvent) via a `POST` request to the `/api/regattas` endpoint. It accepts a `Partial<RegattaDetail>` to allow for flexible initialization of event properties. Use this method when building administrative tools or import workflows that need to instantiate new racing events.

## Invariants

- **Method is `POST`** — Uses `fetchApiAuthenticated` to send a POST request to `/api/regattas`.
- **Payload is `Partial<RegattaDetail>`** — The input must match the shape of the `RegattaDetail` interface (or a subset thereof) to satisfy the API contract.
- **Returns `RegattaDetail`** — On success, the API returns the fully instantiated object, including the server-generated `id` and `event_uuid`.
- **Requires Authentication** — Relies on `fetchApiAuthenticated` to attach the necessary bearer tokens.

## Gotchas

- **`boat_config_id` dependency** — Per commit `bf15808`, the system relies on the `stored boat_config_id` rather than shape-matching to ensure compatibility with the live boat configuration.
- **Type-safety for imports** — Used by `ImportRacesContent` (page.tsx:194); ensure that the `data` passed to `create` aligns with the expected `SailingEvent` or `CustomEventCreate` shapes to avoid runtime errors during bulk imports.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Creating a regatta via this method will update the data used by the "schedule card" and "regatta detail" views.

## External consumers

- `concorda-web::src/app/members/admin/events/import/page.tsx`
- `concorda-web::src/app/members/admin/events/races/[id]/page.tsx`
