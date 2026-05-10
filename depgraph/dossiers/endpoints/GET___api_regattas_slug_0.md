---
node_id: GET::/api/regattas/slug/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5fbf3e6c749127616ecc3abb5a392bacd9ae77ef73ed9648c493ed63e04527e8
status: current
---

# GET /api/regattas/slug/{slug}

## Purpose

Retrieves a single regatta record using its unique URL-friendly slug instead of its database ID. This is the primary method for the frontend to fetch regatta details when navigating via a public or SEO-friendly link. It is distinct from `get_regatta` (which requires a UUID) as it serves as the entry point for public-facing regatta views.

## Invariants

- **Returns `RegattaRead` schema.** The response includes the base regatta data plus embedded match counts.
- **Requires a non-empty `slug` string.**
- **Returns 404 if no match is found.** If the slug does not exist in the database, the API returns a `{"detail": "Regatta not found"}` error.
- **Uses `_attach_counts` for data enrichment.** The return value is processed through `_attach_counts([regatta], db)[0]` to ensure match counts are included in the response.

## Gotchas

- **Relies on `_attach_counts` for critical UI data.** Per commit `e1c7e44` (Regatta match counts — backend), this endpoint was updated to ensure that match counts are embedded in the response, which is essential for the regatta detail view.
- **Slug uniqueness is assumed.** The function uses `.first()`, assuming the slug is a unique identifier in the schema.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible via slug).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The data returned (specifically match counts) is used to populate the regatta detail page and any public-facing regatta overview components.

## External consumers

None known.
