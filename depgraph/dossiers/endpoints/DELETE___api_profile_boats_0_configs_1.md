---
node_id: DELETE::/api/profile/boats/{0}/configs/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 522fcde42007a52e55b3c55dec35f14ba233b23c77d8bebdf7058f74a529fadb
status: llm_drafted
---

# DELETE /api/profile/boats/{boat_id}/configs/{config_id}

## Purpose

Deletes a specific boat configuration associated with a boat and a user's profile. This is a destructive operation used to remove settings that are no longer valid or desired. It is distinct from general boat-level deletions as it targets a specific configuration ID within the context of a specific `boat_id`.

## Invariants

- **Requires `require_auth`** — The request must be authenticated via a valid session/token.
- **Enforces `_require_boat_owner`** — Only the owner of the boat can successfully delete a configuration; unauthorized users receive a 403 or 404 depending on the failure point.
- **Returns `204 No Content`** — On successful deletion, no response body is returned.
- **Strict ID matching** — The `config_id` must match a record that is also linked to the provided `boat_id`.

## Gotchas

- **Cascade logic is sensitive** — Per commit `31aa70d`, changes to boat configurations (including deletions/edits) may require cascading effects to `positions_needed` snapshots and `EventCrew` assignments. Ensure that deleting a config doesn't leave orphaned or broken references in active event snapshots.
- **Single default constraint** — Per commit `09f19fa`, the system enforces a single default configuration per boat. Deleting a configuration that is currently marked as the "default" may require a fallback strategy or will break the assumption that a boat always has an active configuration.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the `_require_boat_owner` guard to ensure ownership.
- **Side effects**: Deleting a config may impact the `positions_needed` snapshot for active sailing events.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deleteBoatConfig`
