---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6bb0e8938028823b1e22c4427bbd6e92fa889a8fc93a793adadae1eb3c4940c1
status: llm_drafted
---

# crewfinderApi.list

## Purpose

Fetches a list of available crew profiles based on specific filters. It is the primary method for populating the "Crewfinder" directory view. Use this instead of `search` when you need a broad list of profiles, as `search` is intended for more complex, multi-faceted queries (returning both crew and boat profiles).

## Invariants

- **Returns a `Promise<CrewfinderProfile[]>`** — the result is a flat array of profile objects.
- **Uses `fetchApiAuthenticated`** — requires a valid session/bearer token to execute.
- **Filters are optional** — `experience_level`, `position`, and `race_area` are all optional and will be appended as URL query parameters if provided.
- **Endpoint is `/api/crewfinder`** — the base path for all crew-related discovery.

## Gotchas

- **Parameter serialization** — The method uses `URLSearchParams` to build the query string. If adding new filter types, ensure they are added to the `searchParams` logic to avoid silent ignores by the API.
- **Dependency on `fetchApiAuthenticated`** — If the authentication helper is modified or the token refresh logic fails, this method will return a 401/403 and break the directory view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Populates the Crewfinder directory view.

## External consumers

None known.
