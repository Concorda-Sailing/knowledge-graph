---
node_id: POST::/api/boats/{0}/share-invite
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 74b810e398b537b969b860718764049b10b2cabc81abc44a2f17cba336b421ac
status: current
---

# POST /api/boats/{boat_id}/share-invite

## Purpose

Mints a single-use, high-entropy share token for a specific boat to facilitate the "crew-link" or QR-code signup flow. The function generates a raw 32-byte URL-safe token, hashes it via SHA-256 for database storage, and returns the unhashed token to the client. This token is intended to be embedded in a QR code or URL, which is later consumed by the registration handler to link a new user to the boat.

## Invariants

- **Requires `require_auth`** — The caller must be an authenticated user.
- **Requires `_require_owner`** — Only the boat owner (not just any crew member) can generate a new share invite.
- **Returns `ShareInviteCreated`** — The response body contains the raw, unhashed `token` string.
- **Uses SHA-256 hashing** — The `invite_token` stored in the database is the hex digest of the raw token to prevent token leakage from DB snapshots.
- **Single-use intent** — While the endpoint creates the record, the consumption logic (not in this function) is responsible for marking the token as used.

## Gotchas

- **Ownership requirement** — Per commit `4c7de14`, the system enforces that the `current_user` must be the Boat Owner to call this. This prevents co-owners or crew from generating invites unless the ownership model is explicitly expanded.
- **Security/IDOR protection** — Per commit `c9a7c41`, the endpoint relies on `_require_owner` to ensure a user cannot generate invites for boats they do not own via boat_id manipulation.
- **Token consumption vs. creation** — This endpoint only *creates* the invite. The actual transition of a user to "crew" status happens in the registration handler (which consumes the token and sets `consumed_at`).

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and `_require_owner` (Boat Owner).
- **Side effects**: The generated token is used by the registration flow to create a `BoatCrew` row with `status='active'` and `role='crew'`.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.createShareInvite` (used for the QR/Share-link UI).
