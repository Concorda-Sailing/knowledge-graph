---
node_id: concorda-test::lib/api-client.ts::ApiClient.createBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d03651b3dbfdd14412858b6496291a816cb2e05b1e1a1df18de98e51b8c1c73
status: current
---

# ApiClient.createBoat

## Purpose

The `createBoat` method handles the creation of a new boat entity associated with the authenticated user's profile. It is a specialized POST request to `/api/profile/boats`. Use this method when a user is transitioning from a "crew" identity to a "captain" identity or when setting up a new vessel for a regatta-related flow.

## Invariants

- **HTTP Method**: Performs a `POST` request to `/api/profile/boats`.
- **Return Shape**: Returns a promise resolving to an object containing the new boat's unique identifier: `{ id: string }`.
- **Authentication**: Requires a valid bearer token established via `ApiClient.login` or `setToken`.

## Gotchas

- **Identity dependency**: Creating a boat is tied to the current authenticated profile. If the `ApiClient` instance is not correctly authenticated, this will fail with a 401/403.
- **Implicit side effects**: Per commit `c8b6d75`, creating/managing boats is a prerequisite for the "Boats tab" and "My Schedule" visibility in integration tests.

## Cross-cutting concerns

- **Auth**: Depends on the bearer token set on the `ApiClient` instance.
- **Side effects**: Successful creation is a prerequisite for the "Boats tab" visibility and populates data used in the "My Schedule" view.

## External consumers

None known.
