---
node_id: concorda-test::lib/api-client.ts::ApiClient.getAvailableProducts
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ec9c5d232219a6533680cddd6cdf8185a5da4f55df84fa324e031228a9cd54a
status: llm_drafted
---

# ApiClient.getAvailableProducts

## Purpose

Fetches the list of available "Temporal Products" from the API. This is a read-only helper used to populate selection menus or displays where users must choose from a predefined set of products (e.g., for onboarding or profile updates). Use this instead of manual fetch calls to ensure the product schema (id, slug, name) remains consistent with the `ApiClient` contract.

## Invariants

- **HTTP Method is `GET`** — performs a standard GET request to `/api/temporal-products/available`.
- **Returns an Array of objects** — each object must contain `{ id: string; slug: string; name: string }`.
- **Requires Authentication** — relies on the `ApiClient` instance having a valid bearer token established via `login()`.

## Gotchas

- **Dependency on remote test host** — per commit `917acfe`, the API client is often pointed at a remote test host rather than a local one; ensure the remote endpoint for `/api/temporal-products/available` is reachable in the current environment.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token (typically established via `ApiClient.login`).
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
