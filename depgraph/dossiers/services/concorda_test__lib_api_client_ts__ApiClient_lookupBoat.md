---
node_id: concorda-test::lib/api-client.ts::ApiClient.lookupBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d28e9e1a158b7944ac7cd942712400b3d8adb74acee25f257dd780d9378487f
status: current
---

# ApiClient.lookupBoat

## Purpose

The `lookupBoat` method performs a search for a specific vessel using its sail number and name. It is used to resolve a human-readable boat identity into a system-recognized `boat_uuid`. This is a critical precursor to the co-owner request flow, allowing a user to identify the correct boat before initiating a formal `requestCoowner` or `coownerInvite`.

## Invariants

- **Method is a GET request** to `/api/boats/lookup`.
- **Input parameters are URL-encoded** via `URLSearchParams` to ensure `sail_number` and `boat_name` are safely passed in the query string.
- **Returns a structured object** containing `exists` (boolean), `boat_uuid` (optional string), `boat_name` (optional string), and `owner_names` (optional array of strings).
- **Requires a valid authenticated session** via the parent `ApiClient` instance to access boat identity data.

## Gotchas

- **Identity resolution is sensitive to exact naming.** Because it relies on both `sail_number` and `boat_name`, partial matches or slight variations in name may result in `exists: false`.
- **Dependency on API stability.** As a direct consumer of the `/api/boats/lookup` endpoint, any change to the expected query parameter keys (`sail_number` vs `sailNumber`) will break the lookup.

## Cross-cutting concerns

- **Auth**: Requires a bearer token from the `ApiClient` instance.
- **Side effects**: Successful lookups are the prerequisite for the `requestCoowner` and `coownerInvite` flows.

## External consumers

None known.
