---
node_id: PUT::/api/profile/boats/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a745a02dcdd9363f968bcc56fdc025915512e1c625c409a904897a94426cc359
status: llm_drafted
---

# PUT /api/profile/boats/{boat_id}

## Purpose

Updates the metadata and configuration for a specific boat. It is used by the profile-side of the application to allow owners to modify boat-specific details like name, registration, and physical dimensions. It is distinct from the creation or deletion endpoints, focusing strictly on the modification of existing `Boat` records.

## Invariants

- **Method is `PUT`** — requires a valid `boat_id` in the URL.
- **Auth is mandatory** — uses `require_auth` to ensure the requester is a logged-in user.
- **Ownership check is strict** — must pass the `_owner_query` check; only the current owner can modify the boat.
- **Field whitelist is enforced** — only fields defined in `BOAT_ALLOWED_FIELDS` (e.g., `name`, `registration_number`, `length`, `positions`) can be updated.
- **Returns `BoatRead` shape** — returns the fully updated boat object.

## Gotchas

- **Strict field filtering** — any keys in the request body not in `BOAT_ALLOWED_FIELDS` are silently ignored by the `setattr` loop.
- **Ownership requirement** — if the user is not the owner, the API returns a `403 Forbidden`. This is a hard requirement for any update attempt.
- **Cascading configuration issues** — per commit `d54327b`, there is a history of reverting changes that attempt to cascade edits to `positions_needed` snapshots or orphan `EventCrew` assignments. Be cautious when modifying how boat configuration changes affect related event/crew data.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `_owner_query` guard.
- **Websocket**: Emits the `BOAT_UPDATED` event via `broadcast_event`.
- **Side effects**: Updates to boat configuration may affect the `positions_needed` snapshot logic (see commit `d54327b`).

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.updateBoat`
- `concorda-test::lib/api-client.ts::ApiClient.updateBoat`
