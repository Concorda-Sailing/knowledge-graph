---
node_id: concorda-web::src/lib/api.ts::seriesApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5d3928c5162716f0275c1ba9fe07b83498178337fb4447765ab57bbddbb6a1ba
status: llm_drafted
---

# seriesApi.update

## Purpose

Updates an existing series record via a `PUT` request. It is used by admin interfaces to modify series-level metadata, such as the `boat_config_id` or `event_subtype`. Use this when you need to modify a specific series rather than creating a new one or generating races for an existing one.

## Invariants

- **HTTP Method is `PUT`** — uses the standard idempotent update pattern.
- **Requires a valid `id`** — the first argument must be the string identifier for the series.
- **Payload is a `Partial<SeriesDetail>`** — only the fields provided in the `data` object will be sent, though the API expects a full representation of the change.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to succeed.

## Gotchas

- **`boat_config_id` vs `boat_uuid`** — per commit `bf15808`, the system was recently fixed to use the stored `boat_config_id` instead of attempting shape-matching. Ensure you are passing the correct ID type for the intended configuration.
- **Schema-driven updates** — the `data` object follows the `Partial<SeriesDetail>` interface; if you attempt to pass fields not present in the `SeriesDetail` definition, the API may reject the request or ignore the field.

## Cross-cutting concerns

- **Auth**: relies on `fetchApiAuthenticated` for bearer token injection.
- **Side effects**: updates to this method will affect the data displayed in the `SeriesDetailContent` component in the admin series page.

## External consumers

None known.
