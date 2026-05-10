---
node_id: concorda-web::src/lib/api.ts::socialsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a643dd05bf3fd0a995b323a496d9057af7bdbdcedb9dc615c67977579b4bad5
status: llm_drafted
---

# socialsApi.list

## Purpose

Fetches the list of social-category events from the API. It is a specialized subset of the general events retrieval, specifically filtered by the `category=social` query parameter. Use this when building views that only require social-type gatherings (e.g., the Socials Page) rather than the full regatta or series-based event lists.

## Invariants

- **Returns `Event[]`** — The response is a collection of event objects.
- **Hardcoded category filter** — Always appends `category=social` to the request path.
- **Uses `fetchApi`** — Unlike the `analyticsApi` siblings in this file, this does not explicitly call a specialized authenticated wrapper, but relies on the underlying `fetchApi` behavior for headers.

## Gotchas

- **Implicit dependency on `category` naming** — The endpoint relies on the string literal `social`. If the backend changes the category name to `social_event` or similar, this list will return empty without a type error.
- **Single consumer dependency** — Currently only consumed by `SocialsPage` (via `page.tsx:260`). Any changes to the return shape of this method will directly break the `SocialsPage` component.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi`, which handles the bearer token injection via the global `ApiClient` state.
- **Side effects**: Primarily affects the rendering of the `SocialsPage`.

## External consumers

None known.
