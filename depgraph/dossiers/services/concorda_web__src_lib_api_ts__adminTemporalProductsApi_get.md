---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 862e76254f5bcc4852ca7cae079b289fef994e31096db88734876bec2cc593c8
status: llm_drafted
---

# adminTemporalProductsApi.get

## Purpose

Fetches a single `TemporalProduct` by its unique identifier. This is a specialized administrative endpoint used to retrieve the full state of a product that exists within a specific temporal window (e.g., a specific year or category). It is distinct from the `list` method, which is used for paginated or filtered collections, and should be used when the UI requires the full object detail for a specific item.

## Invariants

- **Requires a non-empty `id` string.** The function takes a single `id: string` to construct the resource path.
- **Uses `fetchApiAuthenticated`.** All requests must include a valid bearer token to satisfy the administrative authorization requirements.
- **Returns a single `TemporalProduct` object.** The successful response shape is defined by the `TemporalProduct` interface.
- **Path structure is fixed.** The endpoint follows the pattern `/api/temporal-products/${id}`.

## Gotchas

- **Administrative access required.** Because this uses `fetchApiAuthenticated`, the caller must have an active session with appropriate administrative permissions; failure to do so will result in a 401 or 403 error.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level privileges).
- **Side effects**: Changes to the product via sibling methods (`create`, `update`, `delete`) will affect the data returned here.

## External consumers

None known.
