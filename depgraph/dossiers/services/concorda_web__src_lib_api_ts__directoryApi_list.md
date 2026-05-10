---
node_id: concorda-web::src/lib/api.ts::directoryApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ad799a9e22b0afd2da5f7fb8498a304e919a5b0fb57d754949d68963fc16456
status: current
---

# directoryApi.list

## Purpose

Provides a single method to fetch the global list of people in the directory. It is the primary source for the organization's member directory view. Use this instead of `crewfinderApi` or `boatfinderApi` when you need the full, un-filtered list of persons for a general directory listing.

## Invariants

- **Returns `DirectoryPerson[]`** — the response is a collection of person objects.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to resolve the request.
- **GET request to `/api/persons/directory`** — the endpoint is a static path with no query parameters.

## Gotchas

- **Identity-based visibility** — per commit `eb382d2`, the directory is used for "directory-only invite dialogs." Ensure that any UI consuming this list respects the distinction between a general directory view and a specific invitation flow to avoid leaking sensitive context.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: The `DirectoryPage` in `src/app/members/directory/page.tsx` is the primary consumer of this data.

## External consumers

None known.
