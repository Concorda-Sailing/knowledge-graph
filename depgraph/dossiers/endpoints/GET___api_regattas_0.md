---
node_id: GET::/api/regattas/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f71c3ef0b741a4d24602b11d901179a3ce629e4b6074ad13d1b9aceca7c8eed5
status: current
---

# GET /api/regattas/{regatta_id}

## Purpose

Fetches a single regatta's details by its unique identifier. This is the primary endpoint for loading a specific regatta's configuration and metadata. It is distinct from the slug-based lookup (`/slug/{slug}`) which is used for public-facing or SEO-friendly navigation.

## Invariants

- **Returns `RegattaRead` schema.** The response includes embedded match counts via the `_attach_counts` helper.
- **Requires a valid UUID string.** The `regatta_id` must be a valid string representation of a UUID to match the database record.
- **Returns 404 on missing records.** If the ID or slug does not exist, the API raises an `HTTPException` with a 404 status.
- **Uses `_attach_counts` for data enrichment.** The return value is the first element of the list processed by the internal count-attachment helper.

## Gotchas

- **Data enrichment dependency.** The response shape relies on `_attach_counts` (see commit `e1c7e44`) to inject match counts; if this helper is modified or fails, the regatta detail view will break.
- **Slug vs ID lookup.** Developers must ensure they are calling the correct path; `get_regatta_by_slug` is the intended route for public-facing links, whereas this endpoint is for direct ID-based access.

## Cross-cutting concerns

- **Auth**: None (publicly accessible via the router, though the underlying `Regatta` model access may be subject to higher-level security logic).
- **Side effects**: The data returned (specifically the match counts) is used to populate the regatta detail views in the web app.

## External consumers

- `concorda-web::src/lib/api.ts::regattaApi.get`
