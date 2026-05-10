---
node_id: GET::/api/boats/{0}/share-invite/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ccc0d1f1860b6236697c7af78d6833c398cafe5608730d330dea839064e40cce
status: current
---

# GET /api/boats/{boat_id}/share-invite/{invite_token}

## Purpose

Provides the status of a specific boat-sharing invitation. It allows the frontend to poll whether a single-use invite token has been "consumed" (e.g., by a user completing the sign-up flow). This is distinct from the creation endpoint; while the creation endpoint returns the raw token, this endpoint accepts the hashed version of that token to check its lifecycle state.

## Invariants

- **Requires authentication** via `require_auth`.
- **Requires ownership** via `_require_owner(db, boat_id, current_user.id)`.
- **Input is a hashed token.** The `invite_token` passed in the URL must be the SHA-256 hex digest of the raw token, not the raw string itself.
- **Returns `ShareInviteStatus` object.** The shape is `{status: "pending" | "consumed"}`.
- **Returns 404 if the token or boat is not found.**

## Gotchas

- **Token Hashing Requirement:** A common failure mode is passing the raw `invite_token` from the URL/email directly to this endpoint. The function performs `hashlib.sha256(invite_token.encode()).hexdigest()` internally. If the client does not hash the token before calling this, the lookup will fail with a 404.
- **Ownership strictness:** Per commit `4c7de14`, the system enforces that the requester must be a Boat Owner to check the status of an invite. This prevents unauthorized users from probing the existence of active invite tokens.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_owner`.
- **Side effects**: The status change (from `pending` to `consumed`) is the trigger for the frontend "Share Dialog" to refresh the QR code/UI state.

## External consumers

- `concorda-web` (via `boatApi.getShareInviteStatus`)
