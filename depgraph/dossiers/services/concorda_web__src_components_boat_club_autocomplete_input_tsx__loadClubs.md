---
node_id: concorda-web::src/components/boat/club-autocomplete-input.tsx::loadClubs
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 33c2fbabeb1f9be605b39c09767baed56d81cc462e3835261a0cc2dd5f7c76b7
status: current
---

# loadClubs

## Purpose

Fetches and caches the list of organizations (clubs) to populate the autocomplete datalist for the boat location input. It uses a module-level singleton pattern to ensure that only one network request is in flight at a time and that subsequent component mounts reuse the same `Organization[]` list. This prevents redundant API calls to `organizationsApi.list("Yacht Club")` during a single session.

## Invariants

- **Returns a Promise of `Organization[]`**.
- **Uses a module-level cache (`cachedClubs`)** to store the result of the successful fetch.
- **Implements request deduplication** via the `inflight` promise variable.
- **Filters by the hardcoded string `"Yacht Club"`** when calling `organizationsApi.list`.

## Gotchas

- **The search term is hardcoded.** The function specifically calls `organizationsApi.list("Yacht Club")`. If the requirement changes to support different types of organizations (e.g., "Marina" or "Dock"), this function must be refactored to accept a parameter rather than relying on the hardcoded string.
- **The cache is not invalidated.** Once `cachedClubs` is set, it persists for the lifetime of the client-side session. If a new club is added to the database, the user will not see it until they refresh the page.

## Cross-cutting concerns

- **Auth**: Depends on `organizationsApi.list`, which inherits the authentication state of the current session.
- **Side effects**: Populates the datalist for `ClubAutocompleteInput`.

## External consumers

- Internal to `concorda-web`.

## Open questions

- Should `loadClubs` be refactored to accept a `category` argument instead of hardcoding `"Yacht Club"` to allow for more flexible autocomplete inputs in the future?
