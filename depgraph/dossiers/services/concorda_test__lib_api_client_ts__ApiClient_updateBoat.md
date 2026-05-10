---
node_id: concorda-test::lib/api-client.ts::ApiClient.updateBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 60bc569b63d6c09763d123119f04f24751aa3b99972ad665ea45d2bd55910727
status: llm_drafted
---

# ApiClient.updateBoat

## Purpose

The `updateBoat` method performs a partial or full update of an existing boat resource via a `PUT` request. It is the primary way to modify boat metadata (like name or configuration) after the initial creation. Use this when you need to modify an existing boat entity, whereas `createBoat` is reserved for the initial registration of a new boat.

## Invariants

- **HTTP Method is `PUT`** — The method targets the specific resource path `/api/profile/boats/${boatId}`.
- **Requires a `boatId`** — The first argument must be a valid string identifier for the boat being updated.
- **Payload is a `Record<string, unknown>`** — The second argument accepts a dictionary of fields to be updated.
- **Returns `Promise<unknown>`** — The return type is generic, typically reflecting the updated resource or a success confirmation from the API.

## Gotchas

- **Requires valid authentication** — As part of the `ApiClient` suite, this method relies on the bearer token established via `login`. If the token is expired or the session is lost, this will return a 401/403.
- **Identity-dependent updates** — Per commit `c8b6d75`, updates to boat details are often tied to the user's role (e.g., owner vs. crew). Ensure the `ApiClient` instance is authenticated as the correct user to avoid permission errors when modifying boat-specific data.

## Cross-cutting concerns

- **Auth**: Depends on the bearer token stored in the `ApiClient` instance.
- **Rate limit**: None.
- **Side effects**: Updates to boat metadata may trigger UI refreshes in the "Boats" tab (see commit `c8b6d75` regarding crew visibility/data).

## External consumers

None known.

## Open questions

- Should the method signature be more strictly typed than `Record<string, unknown>` to prevent sending invalid schema fields to the `/api/profile/boats` endpoint?
