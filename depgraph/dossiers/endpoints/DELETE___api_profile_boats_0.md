---
node_id: DELETE::/api/profile/boats/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9590d605dc1f424dfe16ef7672325301b3c8725ec40fe5828f9fff613c28bd20
status: llm_drafted
---

# DELETE /api/profile/boats/{boat_id}

## Purpose

Removes the current user's ownership of a specific boat. The behavior is conditional: if the user is the sole owner, the entire `Boat` record and all associated `BoatCrew` rows are deleted from the database. If there are other active owners, the user is simply removed from the `BoatCrew` table.

## Invariants

- **HTTP Method:** `DELETE`.
- **Auth Requirement:** Requires a valid session via `require_auth`.
- **Ownership Check:** Must pass the `_owner_query` check; if the user is not an active owner, the API returns a `403 Forbidden`.
- **Return Shape:** Returns a JSON object with a `message` string (either `"Boat deleted successfully"` or `"Removed from boat ownership"`).
- **Database Integrity:** If the boat is being deleted (sole owner case), all `BoatCrew` rows for that `boat_uuid` are deleted first to prevent orphaned records.

## Gotchas

- **Cascade Logic:** The distinction between "removing self" and "deleting the boat" depends on the `owner_count`. If a developer changes the `BoatCrew` status logic, they may accidentally trigger a full boat deletion when only a membership removal was intended.
- **Commit Timing:** The `db.commit()` occurs twice in the branching logic (once for the full deletion and once for the partial removal).

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the `current_user` is authenticated.
- **Websocket**: Emits `BOAT_DELETED` if the boat is the sole owner, or `BOAT_UPDATED` if only the user's ownership was removed.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers updates to any UI components listening to `BOAT_DELETED` or `BOAT_UPDATED` (e.g., the boat list in the user's profile).

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deleteBoat`

## Open questions

- Should the `owner_count` check include non-active statuses, or is the "sole owner" status strictly tied to the `active` status of the `BoatCrew` role?
