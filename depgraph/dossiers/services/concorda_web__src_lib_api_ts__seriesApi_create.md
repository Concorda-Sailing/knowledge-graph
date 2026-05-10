---
node_id: concorda-web::src/lib/api.ts::seriesApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c78bc3357c9657241442a1d2e154d0c4b0c9475a6be7aa369388f7044314a4c
status: current
---

# seriesApi.create

## Purpose

Creates a new `Series` entity via a POST request to `/api/series`. This is the primary method for initializing a new series of events. Use this when a user is importing or creating a new racing schedule structure that requires a container for subsequent regattas or races.

## Invariants

- **HTTP Method is `POST`** — uses the standard creation pattern for the `/api/series` endpoint.
- **Payload is a `Partial<SeriesDetail>`** — accepts a subset of the full `SeriesDetail` properties.
- **Returns the created `SeriesDetail` object** — the response includes the server-generated `id` and any default fields.
- **Requires authentication** — uses `fetchApiAuthenticated` to ensure the request is tied to a valid user session.

## Gotchas

- **`boat_config_id` dependency** — per commit `bf15808`, the system relies on the stored `boat_config_id` for correct shape-matching; ensure the data passed to `create` includes this if the series is intended to be config-aware.
- **Schema-matching vs. Storage** — per commit `bf15808`, ensure the payload structure matches what the backend expects for a new series to avoid silent failures in downstream component rendering.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Creating a series is a prerequisite for the `ImportRacesContent` flow in the admin/events/import page.

## External consumers

None known.
