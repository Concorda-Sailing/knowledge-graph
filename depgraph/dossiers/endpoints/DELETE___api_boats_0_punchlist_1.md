---
node_id: DELETE::/api/boats/{0}/punchlist/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b81f1a6f9ad4c10c5087ba5d3f1947c5626dd4064b51fc558f73119dc24fbad0
status: llm_drafted
---

# DELETE /api/boats/{boat_id}/punchlist/{item_id}

## Purpose

Deletes a specific item from a boat's punchlist. This endpoint is used when a user needs to remove a task or note from the boat's maintenance or checklist. It is distinct from general boat management as it requires specific ownership or creation rights to prevent unauthorized deletions.

## Invariants

- **HTTP Method is `DELETE`** — targeting `/api/boats/{boat_id}/punchlist/{item_id}`.
- **Requires `require_auth`** — the `current_user` must be authenticated.
- **Strict Authorization** — only the item creator or a user with an "active" role of "owner" can execute the deletion.
- **Returns a success message** — on successful deletion, returns `{"message": "Punchlist item deleted"}`.

## Gotchas

- **Role-based permission sensitivity** — per commit `4c7de14`, the "owner" role is strictly enforced at the time of action. A user must have an "active" membership status and the "owner" role to delete items they did not create.
- **Membership status check** — the `is_active_crew` check (line 126) ensures that even if a user is an owner, if their membership status is not "active" (e.g., pending or declined), they cannot delete punchlist items.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and validates against `_get_crew_membership` for owner/creator status.
- **Websocket**: Emits `PUNCHLIST_UPDATED` with the `boat_id` to notify clients of the change.
- **Side effects**: Deleting an item triggers a UI refresh for any component listening to the `PUNCHLIST_UPDATED` event for that specific boat.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.deletePunchlistItem`

## Open questions

- Should there be a distinction between "soft delete" and permanent deletion for audit purposes, or is immediate DB removal the intended behavior for the punchlist?
