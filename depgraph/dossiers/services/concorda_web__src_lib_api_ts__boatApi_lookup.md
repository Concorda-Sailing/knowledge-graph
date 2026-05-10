---
node_id: concorda-web::src/lib/api.ts::boatApi.lookup
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c498c4e00c9074ffd97105b5cf55352c190298c9cca0a46b657ffa45bee27149
status: current
---

# boatApi.lookup

## Purpose

The `lookup` method performs a search for a boat using a combination of its `sail_number` and `boat_name`. It is used to resolve a boat's identity when a user is searching via a text-based identifier rather than a UUID. This is distinct from `getDetail`, which requires a known `boatId`.

## Invariants

- **Method is GET** — Uses a query string to pass parameters to the `/api/boats/lookup` endpoint.
- **Requires two parameters** — Both `sailNumber` and `boatName` must be provided to construct the `URLSearchParams`.
- **Returns `BoatLookupResult`** — The response shape is defined by the `BoatLookupResult` interface.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute the request.

## Gotchas

- **Search is not UUID-based** — Unlike most boat-related methods in this file that take a `boatId`, this method relies on string-based identifiers.
- **Dependency on `BoatLookupPanel`** — The `BoatLookupPanel` component (at `boat-lookup-panel.tsx:40`) is the primary consumer; changes to the return shape of this method will break the lookup UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Side effects**: Used by `BoatLookupPanel` to resolve boat identities for selection.

## External consumers

- `concorda-web::src/components/boat/boat-lookup-panel.tsx`
