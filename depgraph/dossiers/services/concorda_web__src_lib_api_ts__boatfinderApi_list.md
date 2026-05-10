---
node_id: concorda-web::src/lib/api.ts::boatfinderApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7bda7dacd587cc8787d65d41cd82cbfd51cf94972173b64b4a75907d2eb7b3d3
status: current
---

# boatfinderApi.list

## Purpose

The `boatfinderApi.list` method provides a filtered search of available boats within the `boatfinder` service. It is used to populate the directory of boats available for crew/owner interactions. Use this method when you need to fetch a list of boats filtered by specific criteria like `position`, `race_area`, or `ethos`.

## Invariants

- **GET request** — The method performs a GET request to `/api/boatfinder/search`.
- **Returns `BoatCrewfinderProfile[]`** — The response is a list of boat profiles.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to be present in the session.
- **Optional parameters** — `position`, `race_area`, and `ethos` are all optional and are passed via URL query parameters.

## Gotchas

- **Parameter encoding** — The method uses `URLSearchParams` to build the query string; ensure any custom filter logic remains compatible with standard URL encoding to avoid broken search queries.
- **Dependency on `fetchApiAuthenticated`** — If the authentication header logic changes in the base `fetchApiAuthenticated` function, this list call will fail to return data.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (bearer token required).
- **Side effects**: The results of this call are used to populate the `BoatFinderPanel` component.

## External consumers

- `concorda-web::src/components/finder/boat-finder-panel.tsx`
