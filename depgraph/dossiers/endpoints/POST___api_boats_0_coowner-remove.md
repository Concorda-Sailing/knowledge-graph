---
node_id: POST::/api/boats/{0}/coowner-remove
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 49aff4a0f89d700bb231562301319ec473027e63d16b7a72364f028d5a7e3f1d
status: llm_drafted
---

# POST /api/boats/{boat_id}/coowner-remove

## Purpose

Initiates the removal of a co-owner from a boat. Unlike a direct deletion, this endpoint triggers an approval-based workflow by calling `create_request` with a `boat_coowner_removal` type. This ensures that the removal of a high-privilege user is a tracked event rather than an instantaneous state change.

## Invariants

- **Method/Path**: `POST /{boat_id}/coowner-remove`.
- **Auth**: Requires a valid authenticated user via `require_auth`.
- **Authorization**: The caller must be the owner of the boat, enforced by `_require_owner(db, boat_id, user.id)`.
- **Target Constraint**: The `target_person_uuid` must correspond to a user currently holding the `"owner"` role on the boat.
- **Return Shape**: Returns a JSON object containing the `request_id` of the generated approval request.

## Gotchas

- **Role-based failure**: If the target user is a "crew" member rather than an "owner", the API returns a 404. This is a deliberate guard to prevent using this endpoint to demote standard crew members.
- **Approval-staged workflow**: Per commit `a71ce6c`, this endpoint does not immediately change the user's role; it creates a request. The actual role transition to `"crew"` is handled by the downstream approval logic.
- **Ownership requirement**: The `_require_owner` check is strict. If the user is merely a crew member (even an active one), they cannot trigger this removal.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_owner` to ensure only the boat owner can initiate removal.
- **Audit**: Triggers the creation of an approval request via `services.approvals.create_request`.
- **Side effects**: The resulting request will appear in the approval queues for the organization/boat.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.coownerRemove`
